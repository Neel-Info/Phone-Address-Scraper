import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from playwright.sync_api import sync_playwright
from simple_chalk import chalk
from urllib.parse import urlparse
import re
from bs4 import BeautifulSoup


def get_formatted_url(parsed_url):
    return f'{parsed_url.scheme}://{parsed_url.netloc}{ "/" if not parsed_url.path.startswith("/") else ""}{parsed_url.path}{";" if parsed_url.params != "" else ""}{parsed_url.params}{"?" if parsed_url.query != "" else ""}{parsed_url.query}{"#" if parsed_url.fragment != "" else ""}{parsed_url.fragment}'

def get_phone_number_new_algorithm(line: str):
    """
    Returns the number as a string, if the string only contains phone number
        otherwise it will return an empty string

    Parameters
    -----------
    `line` (str) Input string
    """
    original = line

    line = line.replace('(', '')
    line = line.replace(')', '')
    line = line.replace('-', '')
    line = line.replace(' ', '')
    line = line.replace('.', '')
    line = line.replace(',', '')

    regex = re.compile(r'[+]?\d{10,12}',flags=re.I+re.M)

    test_1 = len(original) >= 10 and len(original) <= 30
    test_2 = regex.search(line)

    tests = [test_1, test_2]

    for test in tests:
        if not test:
            return ''
        
    return original

def read_csv_with_limit(file_path, limit=100):
    """
    Read a CSV file and return the specified number of rows.

    Parameters:
    - file_path (str): Path to the CSV file.
    - limit (int): Number of rows to return. Default is 100.

    Returns:
    - pd.DataFrame: DataFrame containing the specified number of rows.
    """
    df = pd.read_csv(file_path, nrows=limit)
    return df

def get_valid_url(url: str, base = None):
    # <scheme>://<netloc>/<path>;<params>?<query>#<fragment>

    # Add a default prefix if it's missing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    parsed_url = urlparse(url)

    # If the url is a relative url
    if parsed_url.netloc == '' and base != None:
        new_url = urlparse(f'{base.scheme}://{base.netloc}{parsed_url.path}')
        return new_url

    return parsed_url

def remove_tags(html):
 
    # parse html content
    soup = BeautifulSoup(html, "html.parser")
 
    for data in soup(['style', 'script']):
        # Remove tags
        data.decompose()
 
    # return data by retrieving the tag content
    return ' \n'.join(soup.stripped_strings)


def extract_phone(html):
    html_without_tags = remove_tags(html)

    lines = html_without_tags.split('\n')
    numbers = []

    for line in lines:
        result = get_phone_number_new_algorithm(line)

        if len(result) != 0:
            numbers.append(result)

    return list(set(numbers))


def address_round_1(html_without_tags):
    split_string = html_without_tags.split('\n')

    addresses = []
    highly_likely_address = ''
    prev_good = False

    for x in split_string:
        x = x.lstrip().rstrip()
        x = re.sub(' +', ' ', x)

        # ctw_ratio = comma_count / word_count
        if x == '':
            continue

        # this is good code,
        # Please don't delete this...

        if x[-1] == ',':
            highly_likely_address += ' ' + x
            prev_good = True
        elif highly_likely_address != '' and prev_good:
            highly_likely_address += x
            prev_good = False

            c = max(highly_likely_address.count(','), 0)
            w = max(highly_likely_address.count(' '), 1)

            r = c/w
            low = 0.18
            high = 1
            if (r - low) * (high - r) >= 0:
                # print(chalk.green(f'{highly_likely_address} : {c/w}'))
                addresses.append(highly_likely_address)
            else:
                # print(chalk.red(f'Rejecting: {highly_likely_address} : {c/w}'))

                pass

        else:
            highly_likely_address = ''

    return addresses

def address_round_2(html_without_tags, round_1_addresses):
    split_string: str = html_without_tags.split('\n')

    addresses = []
        
    for x in split_string:
        x = x.lstrip().rstrip()
        x = re.sub(' +', ' ', x)

        skip = False
        for address in round_1_addresses:
            if x in address:
                skip = True
                break

        if skip:
            continue

        # ctw_ratio = comma_count / word_count
        if x == '':
            continue

        if x.find(',') == -1:
            continue

        comma_count = x.count(',')
        word_count = x.count(' ') - 1

        wtc_ratio = word_count / comma_count

        if len(x) < 50:
            continue
        zip_regex = re.compile("\d{5,6}|\d{3}.\d{3}", re.M+re.I)
        test = zip_regex.findall(x)
        if len(test) != 0:
            # passed phone number regex, then skip
            y = x
            y = y.replace('(', '')
            y = y.replace(')', '')
            y = y.replace('-', '')
            y = y.replace(' ', '')
            y = y.replace('.', '')
            y = y.replace(',', '')

            regex = re.compile(r'[+]?\d{7,12}',flags=re.I+re.M)
            test_1 = len(regex.findall(y)) == 0
            test_2 = len(x) > 50

            word = max(x.count(' '), 1)
            comma = max(x.count(','), 1)

            ctw_ratio = comma / word

            test_3 = ctw_ratio >= 0.18 and ctw_ratio <= .7

            tests = [
                test_1,
                test_2,
                test_3
            ]

            skip = False

            for test in tests:
                if test == False:
                    skip = True


            if not skip:
                # print(chalk.green(f'{x} : {word_count}/{comma_count} : {wtc_ratio} ___ Len: {len(x)}'))
                addresses.append(x)
            continue

        # print
        if wtc_ratio <= 3:
            # zip_regex = re.compile("\d{5,6}|\d{3}.\d{3}", re.M+re.I)
            # test = zip_regex.findall(x)
            # if len(test) != 0:
            #     print(chalk.green(f'{x} : {word_count}/{comma_count} : {wtc_ratio}'))
            # else:
            splited = x.split(' ')
            nums = sum([ 1 for word in splited if re.search(r'\d', word) != None ])
            words = max(len(splited) - nums - 1, 1)

            ntw = nums/words

            if ntw >= 0.1 and ntw <= 0.7:
                # print(chalk.green(f'{x} : {word_count}/{comma_count} : wtc: {wtc_ratio},  n/w: {nums/words}, len: {len(x)}'))
                addresses.append(x)
            else:
                # print(chalk.red(f'{x} : {word_count}/{comma_count} : {wtc_ratio},  n/w: {nums/words}, len: {len(x)}'))
                pass
        else:
            # split with spaces
            splited = x.split(' ')
            nums = sum([ 1 for word in splited if re.search(r'\d', word) != None ])
            words = max(len(splited) - nums - 1, 1)

            ntw = nums/words

            if ntw >= 0.1 and ntw <= 0.7:
                # print(chalk.green(f'{x} : {word_count}/{comma_count} : wtc: {wtc_ratio},  n/w: {nums/words}, len: {len(x)}'))
                addresses.append(x)
            else:
                # print(chalk.blue(f'{x} : {word_count}/{comma_count} : wtc : {wtc_ratio}, n/w: {nums/words}, len: {len(x)}'))
                pass

    return list(set(addresses))

def remove_substrings(strings):
    result = []
    for i, s1 in enumerate(strings):
        is_substring = False
        for j, s2 in enumerate(strings):
            if i != j and s1 in s2:
                is_substring = True
                break
        if not is_substring:
            result.append(s1)

    return result

def address_round_3(html_without_tags, previous_addresses):
    addresses = []

    splited_string = html_without_tags.split('\n')

    for i, line in enumerate(splited_string):
        zip_regex = re.compile("\d{5,6}|\d{3}.\d{3}", re.M+re.I)

        test_1 = len(zip_regex.findall(line)) != 0

        if not test_1: continue

        y = line

        y = y.replace('(', '')
        y = y.replace(')', '')
        y = y.replace('-', '')
        y = y.replace(' ', '')
        y = y.replace('.', '')
        y = y.replace(',', '')

        # Phone number regex
        regex = re.compile(r'[+]?\d{7,12}',flags=re.I+re.M)
        test_2 = len(regex.findall(y)) == 0

        if not test_2: continue

        x = ''
        for j in range(i, max(0, i-3), -1):
            x = splited_string[j] + x

        address = x[-150:]
        
        if address in addresses:
            continue

        addresses.append(address)

    return addresses


def extract_address(html):
    html_without_tags = remove_tags(html)
    # print(html_without_tags)
    split_string = html_without_tags.split('\n')

    addresses = []

    addresses.extend(address_round_1(html_without_tags))

    addresses.extend(address_round_2(html_without_tags, addresses))

    # addresses.extend(address_round_3(html_without_tags, addresses))

    return remove_substrings(list(set(addresses)))

    ADDRESS_REGEX_1 = re.compile(r'\b\d{1,5}\s\w[^,]+,[^,]+,\s\w{2,}\s\d{5}\b', flags=re.I+re.M)

    regexes = [
        ADDRESS_REGEX_1
    ]

    arr = []

    for regex in regexes:
        result = regex.findall(html_without_tags)
        arr.extend(result)

    return list(set(arr))

def convert_absolute_url_to_relative(url):
    u = urlparse(url)

    return {
        "domain": u.netloc,
        "path": u.path
    }

def get_urls_matching_regex(urls, regex, limit=3):
    """
    Returns a list of about us urls matching the provided regex.

    Parameters:
    urls (list): List of found urls

    Returns:
    List of about us urls matching the regex.
    """
    matching_url = []

    for url in urls:
        if len(re.findall(regex, url)) != 0:
            matching_url.append(url)

    matching_url = list(set(matching_url))

    return matching_url[:min(len(matching_url), limit)]

def get_valid_url(url: str, base = None):
    # <scheme>://<netloc>/<path>;<params>?<query>#<fragment>

    # Add a default prefix if it's missing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    parsed_url = urlparse(url)

    # If the url is a relative url
    if parsed_url.netloc == '' and base != None:
        new_url = urlparse(f'{base.scheme}://{base.netloc}{parsed_url.path}')
        return new_url

    return parsed_url

def useful_links(url, html: str):
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        links = soup.find_all('a')

        hrefs = [link.get('href') for link in links if link.get('href') != None]

        ABOUT_US_REGEX = re.compile(".*a([ -_]?)b([ -_]?)o([ -_]?)u([ -_]?)t([ -_]?)(u([ -_]?)s)?.*", flags=re.I+re.M)
        CONTACT_US_REGEX = re.compile("(c[ _-]?o[ _-]?n[ _-]?t[ _-]?a[ _-]?c[ _-]?t)[ _-]?(u[ _-]?s)?", flags=re.I+re.M)
        CONTACT_US_REGEX2 = re.compile("c[ -_]?o[ -_]?n[ -_]?ta[ -_]?t[ -_]?", flags=re.I+re.M)

        about_us_urls = get_urls_matching_regex(hrefs, ABOUT_US_REGEX, limit=4)
        contact_us_urls = get_urls_matching_regex(hrefs, CONTACT_US_REGEX, limit=4)
        contact_us_urls_2 = get_urls_matching_regex(hrefs, CONTACT_US_REGEX2, limit=4)

        combined = [
            *about_us_urls, 
            *contact_us_urls, 
            *contact_us_urls_2
        ]
        
        combined = list(set(combined))
        filtered = []
        for c in combined:
            if c.startswith('mailto') or c.startswith('tel'): continue
            filtered.append(c)
        combined = filtered

        # <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
        for (i, useful_link) in enumerate(combined):
            parsed_url = urlparse(useful_link)
            if parsed_url.netloc == '':
                combined[i] = f'{url.scheme}://{url.netloc}{ "/" if not parsed_url.path.startswith("/") else ""}{parsed_url.path}{";" if parsed_url.params != "" else ""}{parsed_url.params}{"?" if parsed_url.query != "" else ""}{parsed_url.query}{"#" if parsed_url.fragment != "" else ""}{parsed_url.fragment}'
        # print(chalk.green(combined))
        if(len(combined) == 0):
            print(chalk.red(f'Didnt find any useful links in {url}'))
        else:
            print(chalk.yellow(list(set(combined))[:3]))
                
        return list(set(combined))[:3]
    
    except Exception as e:
        print(f'Error in parsing HTML: {e}')
    finally: 
        pass

