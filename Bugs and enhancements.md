**Search Strategy Example:**
```
For "Sherlock Holmes" in well-known book "A Study in Scarlet" by Arthur Conan Doyle:
- Query 1: "Sherlock Holmes A Study in Scarlet"
- Query 2: "Sherlock Holmes A Study in Scarlet Arthur Conan Doyle"
- Query 3: "Sherlock Holmes illustration"

→ Select top 2-3 most varied results  - This does not work. The selection should be based not of top 2-3 most varied results. The results should be selected based on the mathing to the desired visual style of the book, defined by user. I.e. If the selected style is Sci-fi then the anime- or cartoon- style pics should be excluded. Also 2-3 pics returnd per selection is not a lot, given that the search is rerurning 20 images. So, need to select 5-7 most high rated images. 

Text_image_blending system - implement 

**February 20th**
1. I have edited the search query in the Search Queries tab and they were used in search and recorded in the db - but after navigating back and forth in the application I came back to the review-search page and I see the queries which were there before - make sure always the latest search queries, summary and text_to_image promts are displayed from db. 
2. Refreshing any page in the app brings back to Home page - I want the refresh to keep the position of user in the app. 
3. The style of the book that user is selecting is on 'create-book' is not saved. I.e. when I just uploaded the book I mark it as Science Fiction' but when the book is loaded the UI does not remember this selection and marks the book as 'fiction' by default. Then, I want the list of styles to be grown so that I can have options, i.e. not only sci fi but also Cyberpunk, space opera etc. 
4. The selected style of the book is not included into reference image search query string. 

