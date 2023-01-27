# -*- coding: utf-8 -*-
"""
Created on Tue Jan 17 16:15:56 2023

Amazon Reviews Web Scraping

@author: Josh Phelan
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from random import randint

# Define search query
search_query = "soft+plastic+fishing+lures"

# Define base URL
base_url = "https://www.amazon.com/s?k="

# Complete URL
url = base_url + search_query

# Define user agent and referer for header dictionary
header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:108.0) Gecko/20100101 Firefox/108.0'
          , 'referer':'https://www.amazon.com/s?k=soft+plastic+fishing+lures'}

# Send request based on url and header
response = requests.get(url,headers=header)

# Check if status code is 200 for success
response.status_code

# Storing cookies
cookie = response.cookies

# Beautiful Soup object
soup = BeautifulSoup(response.content)    

# Create list of products by asin number with product name, price, rating and number of ratings for each product
products = []
for j in range(1,26): # first 25 pages of results
    header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:108.0) Gecko/20100101 Firefox/108.0'
              , 'referer':url+'&i=sporting&page='+str(randint(1,30))}
    cookie=response.cookies
    # added search within sporting category for more relevant results
    response=requests.get(url+'&i=sporting&page='+str(j),cookies=cookie,headers=header)
    soup=BeautifulSoup(response.content)

    for i in soup.findAll("div", {'class':"sg-col-4-of-24 sg-col-4-of-12 s-result-item s-asin sg-col-4-of-16 sg-col s-widget-spacing-small sg-col-4-of-20"}):
        product_names = i.find("span", attrs= {'class':"a-size-base-plus a-color-base a-text-normal"})
        price = i.find("span", attrs={'class':'a-offscreen'})
        rating = i.find("span", attrs={'class':'a-icon-alt'})
        no_of_ratings = i.find("span", attrs={'class':'a-size-base s-underline-text'})
        asin = i['data-asin']
        
        
        # Create list of product information for given asin number
        producti=[]
        
        try:
            producti.append(asin)
        except AttributeError:
            producti.append('-')
            
        try:
            producti.append(product_names.text)
        except AttributeError:
            producti.append('-')
        
        try:
            producti.append(price.text)
        except AttributeError:
            producti.append('-')
    
        try:
            producti.append(rating.text)
        except AttributeError:
            producti.append('-')
            
        try:
            producti.append(no_of_ratings.text)
        except AttributeError:
            producti.append('-')
            
    
        # Append list of each product information to products list
        products.append(producti)  

# Convert products list to dataframe
products_df = pd.DataFrame(products, columns = ['asin', 'Name', 'Price', 'Avg Rating', '# of Ratings'])

# Uncleaned dataframe has 576 observations
products_df.shape

# Remove duplicate products by asin number
products_df = products_df.drop_duplicates(subset=['asin']).reset_index(drop=True) #there are 97 duplicates

# Remove products with no reviews because the goal is to collect written reviews of the products
products_df = products_df[products_df['# of Ratings'] != '-'].reset_index(drop=True)

# The data type of all columns is object
products_df.dtypes

# Clean the # of Ratings column and converting the data type to integer
products_df['# of Ratings'] = products_df['# of Ratings'].apply(lambda x: int(x.replace('(','').replace(')','').replace(',','')))

# Clean the Price column and converting the data type to float
products_df['Price'] = products_df['Price'].apply(lambda x: float(str(x[1:])))

# Clean the Avg Rating column and converting the data type to float
products_df['Avg Rating'] = products_df['Avg Rating'].apply(lambda x: float(str(x[:3])))

# Cleaned dataframe has 317 observations
products_df.shape

# Save products dataframe
products_df.to_csv('Data/Products.csv',index=False)






# Scrape all reviews for each product in products table

# Read cleaned products dataframe
products_df = pd.read_csv('Data/Products.csv')

# Create list of all asin numbers
asin_numbers = products_df['asin'].tolist()


# get_link function that uses the asin number to return the product page
def get_link(asin):
    url="https://www.amazon.com/dp/"+asin
    print(url)
    page=requests.get(url,cookies=cookie,headers=header)
    if page.status_code==200:
        return page
    else:
        return "error"

# get_reviews function takes the review link inputted to return the 'See All Reviews' page for that product
def get_reviews(review_link):
    url="https://www.amazon.com"+review_link
    page=requests.get(url,cookies=cookie,headers=header)
    if page.status_code==200:
        return page
    else:
        return "error"


    
    
# Use the get_link function to retrieve the 'See All Reviews' link for each of the asin numbers retrieved
link=[]
for i in range(len(asin_numbers)):
    try:
        cookie = response.cookies
        header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:108.0) Gecko/20100101 Firefox/108.0'
                  , 'referer':"https://www.amazon.com/dp/"+asin_numbers[randint(1,200)]}
        response=get_link(asin_numbers[i])
        print(i)
        if response == "error":
            continue
        else:
            try:
                soup=BeautifulSoup(response.content)
                link.append(soup.find("a",{'data-hook':"see-all-reviews-link-foot"}).get('href'))
            except (TypeError, AttributeError):# occurs when product has no written reviews
                continue
    except (requests.exceptions.SSLError, requests.exceptions.ChunkedEncodingError):
        continue
        
    

# Save list of links to csv
links_df = pd.DataFrame(link,columns=['Link'])
links_df = links_df.drop_duplicates(subset=['Link']).reset_index(drop=True)
links_df.to_csv('Data/Links.csv',index=False)





# Read links dataframe
links_df = pd.read_csv('Data/Links.csv')

# Convert to list
link=links_df['Link'].tolist()

# Traverses the first 25 pages of reviews for each 'See All Reviews' link retrieved 
# For each review, saving the asin, review ID, review title, review body and rating

reviews= []  
for i in range(len(link)):
    for j in range(1,26): # First 25 pages
        try:
            header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:108.0) Gecko/20100101 Firefox/108.0'
                      , 'referer':"https://www.amazon.com/dp/"+asin_numbers[randint(1,200)]}
            cookie=response.cookies
            response=get_reviews(link[i]+'&pageNumber='+str(j))
            soup=BeautifulSoup(response.content)
            for k in soup.findAll('div', attrs={'class':'a-section review aok-relative'}):
                review_id = k['id']
                title = k.find('a', attrs={'class':'a-size-base a-link-normal review-title a-color-base review-title-content a-text-bold'})
                body = k.find('span', attrs={'class':'a-size-base review-text review-text-content'})
                rating = k.find('span', attrs={'class':'a-icon-alt'})
            
                reviewi = []
                
                # Appending the asin to the list
                reviewi.append(link[i].split('/')[3][:10])
                
                try:
                    reviewi.append(review_id)
                except AttributeError:
                    reviewi.append('-')
                    
                try:
                    reviewi.append(title.text)
                except AttributeError:
                    reviewi.append('-')
            
                try:
                    reviewi.append(body.text)
                except AttributeError:
                    reviewi.append('-')
                    
                try:
                    reviewi.append(rating.text)
                except AttributeError:
                    reviewi.append('-')
        
                reviews.append(reviewi)
                
        except (requests.exceptions.SSLError, requests.exceptions.ChunkedEncodingError):
            continue


# Reviews dataframe has 2666 observations before cleaning
reviews_df = pd.DataFrame(reviews, columns = ['asin', 'Review ID', 'Title', 'Body', 'Rating'])

# There were 104 duplicate reviews
reviews_df = reviews_df.drop_duplicates(subset=['Review ID']).reset_index(drop=True)

# Clean the Rating column and converting the data type to float
reviews_df['Rating'] = reviews_df['Rating'].apply(lambda x: float(str(x[:3])))

# No reviews that have a '-' in place of review body text
reviews_df[reviews_df['Body']=='-']

# Save the cleaned reviews dataframe
reviews_df.to_csv('Data/Reviews.csv',index=False)