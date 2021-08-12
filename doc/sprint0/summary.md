# Summary.md #

### One Line Summary: This app will allow UofT students to meet other like-minded students. ###

## Key Objectives ##

- Connecting UofT students together based on similar interests such as music, movies, etc.
- Allow students to meet their peers during the pandemic

## Key Users ##

- Any UofT students that have a valid UofT email
- Some personas we created:
    - Alice Redwood
    - Chad Alpha
    - John Erlich Betaman

## Key Usage Scenarios ##

- To meet like minded individuals that share the same interests in music, games, movies, humour, etc.
- Allows users that are only looking to meet other UofT students to connect with their fellow peers at UofT
- Allows students to find partners for class assignments/projects or other students to study with
- Gives introverts the opportunity to make meaningful connections and build their social network in a more comfortable online way

## Key Principles ##

- The app must be exclusive to only people with a valid UofT email id
- The user should be able to intuitively navigate the app irrespective of their technological experience
- The app finds matches based on given user specifications/preferences and should not use any information beyond that
- The user’s privacy is high priority; any information provided by the user must be kept secure and used only for the purposes of matching
- The app’s core functionality (matching and chatting) should be fully contained in the app without requiring the user to use a third-party service
- UI must be internally consistent and enticing for the user to continue to use the app
- The app must be responsive/snappy and should not lag when users navigates it
- The app must always communicate to the user on what it is currently doing (loading screens, pop ups, etc...)

## Detailed Breakdown of First-Time User Journey: ##

- Users can register an account using their institution email (for now it only works for UofT emails)
- Once an account is created, they will be asked to fill out a short questionnaire, that asks questions such as:
    - Course and program info
    - Favourite music genres
    - Favourite TV shows
    - Favourite food
    - Favourite games
    - Simple personality questions
    - This information will be used to assist with pairing people (more on this explained later)
    - Side Note: We plan to integrate Spotify, Netflix, YouTube, Steam API to automatically pull information from user preference if they allow it
        - We are still researching if this is possible and will plan accordingly

- Now, the user will see predefined memes uploaded by us (developers) that is standardized
    - The user can click one of the buttons for like/dislike/neutral below the meme to potentially match with a user that made decisions in the same order

- We will quantify users’ sense of humour based on the tags of the memes they like/dislike to better match them
- The user will then see a list of other users or groups that have have similar interests to them
- Users can then click their matches to see their profiles that contain a short bio, profile picture, and a summary of their interests (tags), if they click a group they will see a list of the members of that group where they can then click the members to their profiles
- Users within a group can choose to make their group open/closed, and can choose to leave that group. Users that have an ongoing chat can also choose to block the person that they’re chatting with
- If the user is dissatisfied with their questionnaire answers or their meme ratings they can choose to redo the questionnaire or meme ratings to get new matches

## Pairing Methods ##

- We create two different vectors for each user.

    - We will use an approach where we quantify a user's preferences as a vector. 
    - We present memes that the user can like/dislike/neutral. Their decisions are labelled as a 1 (for like), -1 (for dislike), 0 (for neutral). This decision sequence forms a vector.
    - (...Potentially add more methods later on for flexible/accurate pairing)

- We then find the closest distance / cosine similarity between other users. We allow the user to control how close their potential pairs interests need to be by selecting one of the 3 options
    - Strictly similar (distance < ε1) for some small value
    - Mostly similar (distance < ε2) for some larger value
    - Everybody (distance < ∞) 

- We combine both pairs found from methods 1 and 2 and present them to the users. 

- We plan to add app integration, where we can get Spotify taste, YouTube subscription, recently played games etc… Each app will have its own vector that can be compared to each other. If a user does not use one app then that app won't be used in the comparison.  
