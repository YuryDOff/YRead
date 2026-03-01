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

**21 February:**
## 1. The well-known published book should not only try and summarize the book by itself but also include summarization of the plot from available sources (wikipedia or LLM itself)?
+ 2. When I select the genre of the book on "create-book" page as 'Science Fiction' it is not saved to database - and on the next screen of 'customize your experience' the default selection is the 'fiction' while it should be the one I have selected when importing the book - i.e. Science Fiction. 

4. When books are deleted - the reference images are not deleted from the database
5. User inteeface language experience is not cohesive. Looks like the book in Russian has been translated by AI analysis into English, summarised in English - so that the scene analysis is returned from OPenAI model in English even though the original text is in Russian. I want to make sure the cohesive one-language user experience for the user. 
6. For some reason, despite books being deleted from the databsae - same summaries of the characters and locations as before can be seen in the Characters and Locations analysis? Why is that? Should the cache be cleaned?
7. In the lightbox after I have 'liked' the source of the picture on 'books/1/review-search-result' page - no way of saying if the like or dislike has been activated and every press adds a like of dislike. 
8. No way to navigate to the main user dashboard from the user flow. need a 'dashboard' button on every page of the user flow. 
9. 'Customise your experience' title of the 'books/1/create-book' page should be replaced by 'Key Parameters' - or find a similar better title
10. Clicking on 'this is well known published book' gives a empty text box. If this dialogue is turned on I want to be able to add author and the title of the book separately. 
11. The feature called 'Is there another book like it?' should be moved from 'create-book' page to 'books/1/create-book'
12. I want the 'upload your manusctipt' technical name of the page to be called  so (i.e. manuscript-upload rather then create-book). Routes of the interface needs to be uploaded to reflect that. 
13. Image search provider other then SerpAPI and Unsplach are not activated - why not, plan for activating all the search engines mentioned in the requriements_document. 

**February 22nd**
1. Enhancement: I want to rework the visual representation of the 'AI Analysis page' so that full contents of the characters or locations tables were presented in nice visual style. I.e. ontology, type of entity, visual cues, typical emotions etc - all should be represented. Prepare the plan to propose how it may look like 

2. Enhancement: Explore the alogoritm of forming the search string - how does it add up the extracted entity traits (physical appearance, ontology etc) into one cohesive string? What are the rules and how could those be improved? 

3. Enhanceent and documentation: Why do I have 4 search query prompts per character on /books/1/review-search - what is the point? i need to understand the algoritm better.  Can you document the full algorytm of visual pipeline in one picture and include that into documentation? 

4. Bug: Image search engine behavious - Remove limitation of only 1 image returned from Unsplash. I want maxumum amount to be returned. Also, there is no search results from engines other then SERPApi and Unsplash. I want all engines I have APIs keys for (and the ones which do not require this) to provide image search results. I.e. Pexels, Pixabay, Openverse, Wikimedia, Devianart are not returning the reference search images now. 


**February 22nd - 2**
Что изменено в коде
Wikimedia
Добавлен обязательный заголовок User-Agent (требование политики Wikimedia). После этого запросы не должны получать 403.
Openverse
Добавлена опциональная авторизация: если задана переменная окружения OPENVERSE_ACCESS_TOKEN, в запрос подставляется Authorization: Bearer <token>. Токен можно получить через регистрацию/ OAuth2 на Openverse; с токеном лимиты выше и 401 не должны появляться при нормальном использовании.
Pixabay
Со стороны кода и формата запроса всё корректно; 0 результатов — из‑за того, что по такой длинной и конкретной фразе у Pixabay просто нет совпадений. При желании можно позже пробовать укороченный запрос (например, первые 3–4 слова) только для Pixabay, но это уже смена семантики поиска.

Analysis wait screen add the title 'reading, enjoying and analysing the manuscipt' maybe also add an image of AI agent reading the book? 

Organize scenes into 'line graph of hero journey so it is more visual?'

Make sure Openwerse and Wikimedia provide results 

Add functionality to manage the creation of the book cover.

Not all the characters and locations are added into AI analysis. I would like to add to AI analysis the following: 1) extracting all characters and locations. 2) Adding the dramatic class of the character - protagonist, antagonist etc 3) Even if i Add the parameter 'this is a well known book' I don't get the 0 'ontological name'? 

Run implementation pipeline 3 - review the end of the plan before proceeding 