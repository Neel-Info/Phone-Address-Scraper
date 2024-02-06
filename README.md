<div align='center'>
    <img src="./public/img/main-bg.png" width='300px' height='300px'>
</div>

# Phone Address Scraper

<div align='center'>
    <img src="https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54" alt="Python">
    <img src="https://img.shields.io/static/v1?style=for-the-badge&message=Playwright&color=2EAD33&logo=Playwright&logoColor=FFFFFF&label=" alt="Playwright">
</div>

This codebase contains python scripts using Playwright, BeautifulSoup and Pandas, to read domains from a CSV file and scrape those domains to find out Phone numbers and addresses from their home page and other links like about page, contact page.

## Algorithm

### Phone Number Extraction

I have used to following algorithm to extract phone numbers from website's html code.

<ol>
    <li> Request the page using Playwright library </li>
    <li> Parse the html content using beautiful soup </li>
    <li> Split the string using <code>\n</code> character </li>
    <li> For each string in space separated list 
        <ul>
            <li>Remove all the characters like <code>(),-+.</code></li>
            <li>Now use a regex <code>[+]?\d{10,12}</code> to find out consecutive 10-12 numbers</li>
            <li>If such regex match is found, add it to <code>phone_numbers</code> list.</li>
        </ul>
    </li>
    <li> Return <code>phone_numbers</code> </li>
</ol>

### Address Extraction

Algorithm for extracting addresses.

<ol>
    <li>Request the page using Playwright library</li>
    <li>Parse the html content using beautiful soup</li>
    <li>Split the string using <code>\n</code> character</li>
    <li> For each string in space separated list 
        <ul>
            <li>Count the number of words and comma in the line</li>
            <li>Let <code>w</code> be the number of words, and <code>c</code> be the number of comma</li>
            <li>Count <code>c/w</code> and if it is in range of <code>0.18</code> and <code>1</code>, it is highly likely to be a address.</li>
        </ul>
    </li>
    <li> Return <code>phone_numbers</code> </li>
</ol>

> **_Note :_** These algorithms are designed to overestimate, meaning that it will consider a larger category of text as phone numbers and address. For example, 192.168.10.255 is an IP address but it might that other website shows phone number in this format like 180.655.655.200. Similar argument can be made with address. It is better to take a larger, more general filter to estimate phone numbers and addresses, since it is possible to make granular filters later which could be run on the extracted phone numbers and addresses to fine tune the output.
