# Model Card: Music Recommender Simulation

## 1. Model Name

**VibeFinder 1.0**

---

## 2. Intended Use

VibeFinder suggests the top 5 songs from a small catalog based on a user's preferred genre,
mood, and energy level. It is a classroom simulation — not intended for real users or
production deployment. It exists to explore how simple rule-based scoring produces
recommendation behavior similar to what large platforms like Spotify do at much greater scale.

---

## 3. How the Model Works

For each song in the catalog, VibeFinder computes a numeric "match score" against the user's
stated preferences:

- **Genre** is worth the most (2 points). If the song's genre matches yours, it jumps ahead of
  most other songs immediately.
- **Mood** is worth 1 point. A song that matches your emotional vibe gets a boost.
- **Energy closeness** contributes up to 1 point. The closer a song's energy level is to your
  target, the higher it scores — a perfect energy match adds a full point, a huge gap adds
  almost nothing.
- **Acoustic bonus** (0.5 points) is only awarded if the user has flagged that they enjoy
  acoustic music *and* the song scores high on acousticness.

After every song is scored, the list is sorted from highest to lowest and the top 5 are
returned with a plain-language explanation for each match.

---

## 4. Data

The catalog (`data/songs.csv`) contains **30 songs** across 12 genres: pop, lofi, rock,
synthwave, jazz, ambient, indie pop, country, electronic, acoustic, r&b, and hip-hop.
Moods include happy, chill, intense, relaxed, focused, and moody.

The original starter dataset had 10 songs; 20 were added to improve variety. Despite the
expansion, some genres (lofi, pop, rock, ambient) have more entries than others (country,
jazz, r&b), so users with those preferred genres have more candidates to score against.
The dataset reflects a fairly mainstream Western pop/rock taste and does not include
classical, world music, or non-English language genres.

---

## 5. Strengths

- **Clear, predictable genre users** — a "rock/intense" or "lofi/chill" profile reliably
  surfaces songs that intuitively feel like a good match because both the genre and mood
  dimensions align.
- **Transparent explanations** — every recommendation comes with a printed reason list, making
  it easy to understand exactly why a song was ranked where it was.
- **Tunable weights** — passing a custom `weights` dict to `recommend_songs` lets you quickly
  test how changing the importance of genre vs. energy changes the output without touching
  the core logic.

---

## 6. Limitations and Bias

**Genre over-weighting creates a filter bubble.** Genre is worth 2 points — double any other
single factor. This means a song that matches your genre but completely misses your mood and
energy can still outrank a song that nails your mood and energy but belongs to a neighboring
genre. For example, asking for "ambient + intense + high energy" surfaces quiet, chill ambient
tracks at the top simply because they match the genre label, while truly intense high-energy
songs from rock or electronic genres are pushed down.

**No diversity enforcement.** The top 5 results can all be from the same artist or the same
sub-niche within a genre. A real recommender would penalize repetition to surface a variety
of artists.

**Energy is treated as a single number.** A user who wants "energetic morning music" and a
user who wants "background focus music" might both set `energy: 0.75`, but they want very
different things. The model cannot distinguish between these contexts.

**Small and skewed catalog.** With only 30 songs, a user whose preferred genre has only 2–3
entries will always get the same songs in their top 5, regardless of how well those songs
actually fit. The system also has no country, jazz, r&b, or hip-hop mood variety — all four
genres have just one mood represented.

---

## 7. Evaluation

Four user profiles were tested:

| Profile | Genre | Mood | Energy | Key observation |
|---|---|---|---|---|
| High-Energy Pop | pop | happy | 0.85 | Results felt accurate — "Carnival Keys" and "Sunrise City" ranked #1–2 as expected |
| Chill Lofi Study | lofi | chill | 0.38 | All top 3 were lofi/chill; acoustic bonus surfaced quieter tracks correctly |
| Deep Intense Rock | rock | intense | 0.90 | "Storm Runner" and "Wildfire Heart" tied at ~3.99; results matched intuition perfectly |
| Adversarial: Ambient + Intense | ambient | intense | 0.90 | **Surprising** — quiet ambient songs ranked above intense rock/electronic tracks because the genre bonus (+2) overwhelmed a 0.62-point energy gap |

**Weight-shift experiment (Profile 4):** Halving the genre weight to 1.0 and doubling the
energy weight to 2.0 flipped the adversarial profile: high-energy rock and electronic songs
rose to the top, which better matched the stated "intense + high energy" intent. This
confirmed that default weights are tuned for typical users but fail users whose genre choice
conflicts with their other preferences.

No automated metrics were used. Correctness was evaluated by comparing the ranked list to
what a human listener with those stated preferences would likely expect.

---

## 8. Future Work

- **Soften the genre constraint** — use a genre *similarity* score instead of a hard match
  (e.g., "indie pop" and "pop" should be closer than "pop" and "metal").
- **Add diversity penalty** — reduce the score of songs by the same artist if they already
  appear in the top results, to prevent one artist dominating every list.
- **Tempo range preference** — let users specify a BPM range (e.g., 80–110 for focus work)
  rather than relying on energy alone.
- **Learned weights** — instead of hard-coded weights, tune them per user based on which
  recommendations the user accepted or skipped.

---

## 9. Personal Reflection

Building VibeFinder made the genre-weighting bias immediately visible in a way that just
reading about recommender systems never could. The adversarial profile test was the clearest
moment: a user asking for "intense, high-energy music" ended up with a playlist of quiet
ambient tracks simply because of a label match. That gap between what a label says and what
a song actually sounds like is exactly the problem real platforms solve with audio features
and listening history — neither of which this simulation uses.

The experiment of shifting the weights also showed how much power a single number has over
the entire output. Changing genre from 2.0 to 1.0 completely changed who the top
recommendations were. That makes me think about how consequential weight choices are in
real AI systems — and how those choices are usually made by engineers, not the users who
experience the results.
