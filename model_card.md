# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name

Give your model a short, descriptive name.  
Example: **VibeFinder 1.0**

---

## 2. Intended Use

Describe what your recommender is designed to do and who it is for.

Prompts:

- What kind of recommendations does it generate
- What assumptions does it make about the user
- Is this for real users or classroom exploration

---

## 3. How the Model Works

Explain your scoring approach in simple language.

Prompts:

- What features of each song are used (genre, energy, mood, etc.)
- What user preferences are considered
- How does the model turn those into a score
- What changes did you make from the starter logic

Avoid code here. Pretend you are explaining the idea to a friend who does not program.

---

## 4. Data

Describe the dataset the model uses.

Prompts:

- How many songs are in the catalog
- What genres or moods are represented
- Did you add or remove data
- Are there parts of musical taste missing in the dataset

---

## 5. Strengths

Where does your system seem to work well

Prompts:

- User types for which it gives reasonable results
- Any patterns you think your scoring captures correctly
- Cases where the recommendations matched your intuition

---

## 6. Limitations and Bias

Where the system struggles or behaves unfairly.

Prompts:

- Features it does not consider
- Genres or moods that are underrepresented
- Cases where the system overfits to one preference
- Ways the scoring might unintentionally favor some users

Earlier genres were more represented and energy was underrepresented. After running the data experiment, energy domintes the scoring. It weights energy at 4, while genre and mood are weighted at 1.
The system also looks for exact genre and mood matches, which may not capture users with more flexible tastes. For example, calm and chill can be similar moods, but the system treats them as completely different.
Additionally, the dataset has sparse coverage of some tastes like rocj, jazz, and indie pop. It also has a uneven distribution of moods - chill appears multiple times, while focused only appears once. This could lead to recommendations that favor more common genres and moods, while neglecting niche preferences.

---

## 7. Evaluation

How you checked whether the recommender behaved as expected.

Prompts:

- Which user profiles you tested
  - High-Energy Pop: genre=pop, mood=happy, high target energy.
  - Chill Lofi: genre=lofi, mood=chill, low target energy.
  - Deep Intense Rock: genre=rock, mood=intense, high target energy.
  - Edge/adversarial profiles: unknown genre+mood, case-mismatch inputs, missing/NaN energy.
- What you looked for in the recommendations
  - Top songs should match user's profile preferences.
  - Similar profiles should get similar rankings, but not identical.
  - Explanations should reflect the scoring logic (e.g., energy should have a strong influence on scores).

- What surprised you
  - Some songs with genre mismatch ranked higher than genre matched when energy was close to the target.
  - Exact string comparisons lead to case sensitivity issues, causing some expected matches to be missed.

- Any simple tests or comparisons you ran
  - Compared the baseline scoring logic to the modified version with energy weighting to see how rankings changed.
  - Tested edge cases like missing energy values to see how the system handled them.
  - Checked for diversity in recommendations across different user profiles.

## No need for numeric metrics unless you created some.

## 8. Future Work

Ideas for how you would improve the model next.

Prompts:

- Additional features or preferences
- Better ways to explain recommendations
- Improving diversity among the top results
- Handling more complex user tastes

---

## 9. Personal Reflection

A few sentences about your experience.

Prompts:

- What you learned about recommender systems
- Something unexpected or interesting you discovered
- How this changed the way you think about music recommendation apps
