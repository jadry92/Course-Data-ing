import argparse
import pandas as pd
import logging
import hashlib
import re
import nltk

from urllib.parse import urlparse
from nltk.corpus import stopwords

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
STOP_WORDS = set(stopwords.words('spanish'))


def main(filename):
    logger.info('Starting the cleaning process')

    df = _read_data_from_csv(filename)
    newspaper_uid = _extract_newspaper_uid(filename)
    df = _add_newspaper_uid_column(df, newspaper_uid)
    df = _extract_host(df)
    df = _filling_up_missing_titles(df)
    df = _generate_uids_from_rows(df)
    df = _remove_special_characters(df, 'title')
    df = _remove_special_characters(df, 'body')
    df = _tokenize_columns(df, 'title')
    df = _tokenize_columns(df, 'body')
    df = _remove_duplicate_entries(df, 'title')
    df = _drop_rows_with_missing_data(df)
    _save_data(df, filename)
    return df


def _read_data_from_csv(filename):
    logger.info('Reading file {}'.format(filename))

    return pd.read_csv(filename)


def _extract_newspaper_uid(filename):
    logger.info('Extracting newspaper UID')

    newspaper_uid = filename.split('_')[0]
    logger.info('Newspaper uid detected: {}'.format(newspaper_uid))

    return newspaper_uid


def _add_newspaper_uid_column(df, newspaper_uid):
    logger.info('Filling newspaper_uid column with {}'.format(newspaper_uid))

    df['newspaper_uid'] = newspaper_uid
    return df


def _extract_host(df):
    logger.info('Extracting host from urls')

    df['host'] = df['url'].apply(lambda url: urlparse(url).netloc)
    return df


def _filling_up_missing_titles(df):
    logger.info('Filling up missing titles')

    missing_titles_mask = df['title'].isna()
    missing_titles = (df[missing_titles_mask]['url']
                      .str.extract(r'(?P<missing_titles>[^/]+)$')
                      .applymap(lambda title: title.split('-'))
                      .applymap(lambda title_word_list: ' '.join(title_word_list))
                      )
    df.loc[missing_titles_mask, 'title'] = missing_titles.loc[:, 'missing_titles']
    return df


def _generate_uids_from_rows(df):
    logger.info('Generation uids for each row')
    uids = (df
            .apply(lambda row: hashlib.md5(bytes(row['url'].encode())), axis=1)
            .apply(lambda hash_object: hash_object.hexdigest())
            )
    df['uid'] = uids
    df.set_index('uid', inplace=True)
    return df


def _remove_special_characters(df, column):
    logger.info('Removing the special characters in {} column'.format(column))

    new_serie = (df
                 .apply(lambda row: row[column], axis=1)
                 .apply(lambda text: re.sub(r'(\n|\r)+', r'', text))
                 )
    df[column] = new_serie
    return df


def _tokenize_columns(df, column):
    logger.info('Counting the number of words in the {} column'.format(column))
    global STOP_WORDS
    tokens_series = (df.dropna()
                     .apply(lambda row: nltk.word_tokenize(row[column]), axis=1)  # return a list with all the words
                     .apply(lambda tokens: list(filter(lambda token: token.isalpha(), tokens)))  # return a list with only alphanumeric words
                     .apply(lambda tokens: list(map(lambda token: token.lower(), tokens)))  # change all the words to lowercase
                     .apply(lambda word_list: list(filter(lambda word: word not in STOP_WORDS, word_list)))  # clear all the stop words
                     .apply(lambda valid_word_list: len(valid_word_list))
                     )
    tokens_column = 'n_tokens_{}'.format(column)
    df[tokens_column] = tokens_series
    return df


def _remove_duplicate_entries(df, column):
    logger.info('Removing duplicate entries')
    df.drop_duplicates(subset = [column], keep='first', inplace=True)

    return df


def _drop_rows_with_missing_data(df):
    logger.info('Dropping rows with missing values')
    return df.dropna()


def _save_data(df, filename):
    clean_filename = 'clean_{}'.format(filename)
    logger.info('Saving data at location: {}'.format(clean_filename))
    df.to_csv(clean_filename, encoding='utf-8-sig')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'filename',
        help='the path of the dirty data',
        type=str
    )
    args = parser.parse_args()

    df = main(args.filename)
    print(df)