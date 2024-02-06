from utils.my_util import *

# Define your functions to find phone numbers, addresses, and useful links
def find_phone_number(html):
    x = extract_phone(html)
    return x

def find_address(html):
    x = extract_address(html)
    return x

def find_useful_links(url, html):
    return useful_links(url, html)

def process_url(url):
    with sync_playwright() as p:
        try:
            parsed_url = get_valid_url(url)
            formatted_url = f'{parsed_url.scheme}://{parsed_url.netloc}{ "/" if not parsed_url.path.startswith("/") else ""}{parsed_url.path}{";" if parsed_url.params != "" else ""}{parsed_url.params}{"?" if parsed_url.query != "" else ""}{parsed_url.query}{"#" if parsed_url.fragment != "" else ""}{parsed_url.fragment}'

            browser = p.chromium.launch()
            print(formatted_url)
            context = browser.new_context()
            page = context.new_page()
            page.goto(formatted_url)
            page.wait_for_load_state('networkidle')

            html_content = page.content()

            # phone_numbers = find_phone_number(html_content)
            # addresses = find_address(html_content)
            phone_numbers = []
            addresses = []
            useful_links = find_useful_links(parsed_url, html_content)

            for link in useful_links:
                # Visit each useful link and extract phone numbers and addresses
                try:
                    new_url = get_valid_url(link)
                    formatted_new_url = f'{new_url.scheme}://{new_url.netloc}{ "/" if not (new_url.path.startswith("/") and new_url.netloc.endswith("/")) else ""}{new_url.path}{";" if new_url.params != "" else ""}{new_url.params}{"?" if new_url.query != "" else ""}{new_url.query}{"#" if new_url.fragment != "" else ""}{new_url.fragment}'
                    page.goto(formatted_new_url)
                    page.wait_for_load_state('networkidle')

                    link_html_content = page.content()
                    phone_numbers.extend(find_phone_number(link_html_content))
                    addresses.extend(find_address(link_html_content))
                except Exception as e:
                    print(chalk.red(f'Error inside: {e}'))

            return {'url': url, 'phone_numbers': phone_numbers, 'addresses': addresses}
        except Exception as e:
            print(chalk.red(f'Error: {e}'))
        finally:
            page.close()
            context.close()
            browser.close()
            return {'url': url, 'phone_numbers': [], 'addresses': []}


def main():
    # Read CSV file with pandas
    input_file = 'data/28k.csv'
    df = read_csv_with_limit(input_file, limit=1)

    # Create a thread pool with max_workers=20
    with ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(process_url, df['Domain']))

    # Store results in a new DataFrame
    result_df = pd.DataFrame(results)

    # Save the results to a new CSV file
    result_df.to_csv('out/output_results.csv', index=False)


if __name__ == "__main__":
    main()
