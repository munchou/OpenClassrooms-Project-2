import requests
from bs4 import BeautifulSoup
import csv
from pathlib import Path
import re
import os
import time

start_time = time.perf_counter()

main_url = "https://books.toscrape.com/"
catalog_url = "http://books.toscrape.com/catalogue/"

#Getting the type of category to make an output file for each category such as "urls_Category"
index = requests.get(main_url)
categories_links = []
if index.ok:
    soup = BeautifulSoup(index.text, 'html.parser')
    cat_list = soup.find('div', {'class': 'side_categories'}).find_all('li')
    for linkou in cat_list:
        a = linkou.find('a')
        linkz = a['href']
        categories_links.append(main_url + linkz)

#Note: the [1:] is to skip the first category that regroups ALL the books of the website
for link_to_category in categories_links[1:]:
    page = requests.get(link_to_category)
    category_mystery = link_to_category
    links = []

    #Getting the type of category (will be used for the creation of the directory as well as the output CSV file)
    if page.ok:
        soup = BeautifulSoup(page.text, 'html.parser')
        cat_name = soup.find('li', class_='active').text
        print("Current category: " + cat_name)


    #Extracting the links depending on if there are several pages or only one
    if page.ok:
        soup = BeautifulSoup(page.text, 'html.parser')
        next_page = soup.findAll('ul', class_='pager')

    #More than one page:
        if len(next_page) >=1 :
            for num_of_pages in next_page:
                num_of_pages2 = num_of_pages.find('li', class_="current").text
                test = num_of_pages2.strip()[10:]
                test2 = int(test)+1
                print(f"This category has {test2-1} pages in total.")
                
                for i in range(1, test2):
                    url2 = category_mystery.replace('index.html', '') + f"page-{str(i)}.html"
                    page2 = requests.get(url2)
                    print(page2)
                    print(url2)
                    if page2.ok:
                        print("Page: " + str(i))
                        soup = BeautifulSoup(page2.text, 'html.parser')
                        book_title = soup.findAll('article', class_='product_pod')
                        for titlelink in book_title:
                            a = titlelink.find('a')
                            book_link = a['href']
                            links.append(catalog_url + book_link[9:])

    #Only one page:
        else:
            url2 = category_mystery
            page2 = requests.get(url2)
            print(page2)
            if page2.ok:
                soup = BeautifulSoup(page2.text, 'html.parser')
                book_title = soup.findAll('article')
                for titlelink in book_title:
                    a = titlelink.find('a')
                    book_link = a['href']
                    links.append(catalog_url + book_link[9:])

    #Creating the directories for the books' categories and the books' covers
    directory = f"{cat_name}"
    parent_dir = "./"
    pathtest = os.path.join(parent_dir, directory)
    img_dir = os.path.join(cat_name, "Books Covers")
    try: #to check if the directory already exists and bypass the fact that it already exists
        os.makedirs(pathtest, exist_ok = True)
        os.makedirs(img_dir, exist_ok = True)
        print("Directory '%s' created successfully" %directory)
        print(f"Directory {img_dir} created successfully")
    except OSError as error:
        print("Directory '%s' could not be created")
        print(f"Directory {img_dir} could not be created")
    
    #Writing the headers in the CSV file with the category's name
    with open(f"{pathtest}/{cat_name}.csv", 'w', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file, delimiter=',')
        writer.writerow([
                    "Product's page url",
                    "Universal Product Code (UPC)",
                    "Book's title",
                    "Price (including tax)",
                    "Price (excluding tax)",
                    "Number available",
                    "Product description",
                    "Category",
                    "Review rating",
                    "Image's url"
                ])

#*******************************************************************************
#SCRAPING BOOKS ONE BY ONE
#*******************************************************************************
    for booklink in links:
        page = requests.get(booklink)
        soup = BeautifulSoup(page.content, 'html.parser', from_encoding="utf-8")
        
        
        #Retrieving the info content
        product_info = soup.find_all('td')
        p = soup.find_all('p')
        
        upc = product_info[0].text
        title = soup.find('h1').text
        price_inc_tax = product_info[3].text
        price_exc_tax = product_info[2].text
        avail = product_info[5].text
        number_available = avail.replace('In stock (', '').replace(')', '')
        try:
            product_description = soup.find('div', {'id': 'product_description'}).find_next('p').text.replace('...more', '')
        except:
            print("This book doesn't have a descrption.")
            product_description = "No description"
        category = soup.find_all('a')[3].text
        review_rating = f"{p[2]['class'][1]} stars"
        if f"{p[2]['class'][1]}" == "One":
            review_rating = "One star"
        
        #Getting a clean title without special characters and without losing the spaces
        clean_title = ""
        for k in title.split("\n"):
            clean_title = " ".join(re.findall(r"[a-zA-Z0-9']+", k))
        print("Extracting " + category +" / " + clean_title)
        
        #Image URL
        main_img_url = f"{main_url}{soup.find('div', id='product_gallery').find('img')['src'][6:]}"
        
        #Downloading the image
        #Note: "stream=True" guarantees no interruptions will occur when the method is running
        #imgurl = f"{main_url + soup.find('img')['src'][6:]}"
        imgurl = main_url + f"{soup.find('img')['src'][6:]}"
        imgdl = requests.get(imgurl, stream = True)
        #Use of Path (pathlib) to get the whole url of the image, then keep only the final segment, which is the original name of the jpg file
        #img_path = Path(imgurl).parts[-1]
        #getimg = open(f"{img_dir}/{img_path}", 'wb')
        #Change of plan: give the images the name of their respective books
        getimg = open(f"{img_dir}/{clean_title}.jpg", 'wb')
        getimg.write(imgdl.content)
        getimg.close()

        #Exporting the data to the CSV file, use of 'a' to ADD into the file
        with open(f"{pathtest}/{cat_name}.csv", 'a', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file, delimiter=',')
            writer.writerow([
                booklink,
                upc,
                title,
                price_inc_tax,
                price_exc_tax,
                number_available,
                product_description,
                category,
                review_rating,
                main_img_url
            ])
        print("Successfully extracted " + clean_title + ".")
        print("*******************************************")

elapsed_time = time.perf_counter() - start_time
elapsed_time_min = int(elapsed_time/60)
print(f"The whole process took {elapsed_time_min} minutes and {round(elapsed_time - (60*elapsed_time_min), 2)} seconds.")

#Saving the elapsed time in a txt:
with open(f"elapsed_time.txt", 'w', encoding='utf-8') as file:
    file.write(f"The whole process took {elapsed_time_min} minutes and {round(elapsed_time - (60*elapsed_time_min), 2)} seconds.")