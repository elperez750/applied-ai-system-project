# Reflection: Profile Comparison Notes

## Profile 1 vs Profile 2 — High-Energy Pop vs Chill Lofi

These two profiles are near-opposites in every dimension: one wants loud, danceable pop at
energy 0.85, the other wants quiet, focused lofi at energy 0.38. The results reflected that
perfectly — they shared zero songs in their top 5. The pop profile surfaced "Carnival Keys"
and "Sunrise City" (bright, uptempo, high-danceability), while the lofi profile produced
"Library Rain," "Midnight Coding," and "Rainy Afternoon" (low energy, high acousticness,
study-friendly). This makes intuitive sense: genre and mood both matched strongly, and the
energy gap between the two target levels (0.85 vs 0.38) is large enough that even a song
with no genre or mood match could not cross over.

The one small surprise: the lofi profile with `likes_acoustic: True` gave a slight bonus to
high-acousticness tracks, which gently pushed "Library Rain" above "Midnight Coding" even
though their energy scores were nearly identical. That is a subtle but accurate distinction —
"Library Rain" (acousticness 0.86) does sound more acoustic than "Midnight Coding" (0.71).

**Takeaway:** When genre, mood, and energy all point in the same direction, the recommender
works well. The profiles feel like genuinely different listeners, and the outputs feel like
genuinely different playlists.

---

## Profile 2 vs Profile 3 — Chill Lofi vs Deep Intense Rock

Both profiles have very clear, internally consistent preferences — just at opposite ends of
the energy and mood spectrum. The lofi listener gets soft, slow tracks under 80 BPM; the
rock listener gets tracks above 130 BPM with high energy scores. Again, no overlap in the
top 5.

What is interesting to compare is how tight the scores are within each list. The lofi top 3
(Library Rain, Midnight Coding, Rainy Afternoon) all scored between 3.95 and 3.97 — nearly
identical. The rock top 2 (Storm Runner, Wildfire Heart) both scored ~3.99. This is because
the catalog has just enough lofi/chill and rock/intense songs to fill out the top 3–4 slots,
but the fifth-place results start to drop off as the system runs out of perfect matches and
falls back to energy-only similarity.

**Takeaway:** The recommender rewards users whose preferred genre has several songs in the
catalog. Lofi and rock both have 4–5 songs, so both profiles produce satisfying results.
A user wanting country or jazz would only have 1–2 genre-matching songs and would see a
weaker top-5.

---

## Profile 3 vs Profile 4 — Deep Intense Rock vs Adversarial (Ambient + Intense)

This is the most revealing comparison. Profile 3 (rock/intense/high-energy) and Profile 4
(ambient/intense/high-energy) differ only in genre. You might expect similar playlists since
they want the same mood and energy. Instead, they produced completely different — and in
Profile 4's case, wrong-feeling — results.

Profile 3 correctly surfaces "Storm Runner" and "Wildfire Heart" — exactly the kind of
aggressive, fast rock tracks you would expect.

Profile 4, using default weights, surfaced quiet ambient songs like "Petal Storm" and
"Spacewalk Thoughts" at the top — songs with energy around 0.25–0.30, even though the user
asked for energy 0.90. Why? Because the genre match (+2.0) for "ambient" outweighed the
energy gap penalty. A song at energy 0.28 targeting 0.90 only loses (1.0 - 0.62 =) 0.38
points on energy, but gains 2.0 points on genre — a net benefit of +1.62, which is enough
to beat any non-ambient song.

Imagine explaining this to someone who does not code: it is like telling a store clerk "I
want something loud and exciting in the jazz section" and they hand you a quiet ballad
because it was in the jazz section — and that location label mattered more to them than what
the music actually sounds like.

**The experiment fix:** Changing the weights to `genre: 1.0, energy weight: 2.0` corrected
this. The high-energy intense tracks from rock and electronic now rose to the top of Profile
4's list because the energy gap cost more than the genre bonus was worth.

**Takeaway:** The adversarial profile exposed the single biggest design flaw in the system.
Genre is used as a rigid categorical gate, not as a soft signal. Real recommenders avoid
this by treating genre as one audio signal among many, not as a fixed multiplier.

---

## Why Does "Gym Hero" Keep Appearing for Happy Pop Fans?

"Gym Hero" (pop, intense, energy 0.93) is a pop song, so it gets the full genre bonus (+2.0)
for any pop-preferring user. Even though its mood is "intense" — not "happy" — it scores
highly because the genre match alone pushes it near the top.

Think of it this way: imagine you asked a friend to pick "happy pop songs" from a big pile
of CDs. Your friend sees the "pop" label and automatically moves it to the yes pile, then
notices it says "intense" on the back and thinks "well, it is still pop." The genre label
acts like a VIP pass that gets songs into consideration even when the other details are off.

This is a real phenomenon in music platforms too. A song can end up recommended to someone
who would never actually enjoy it, simply because it shares a genre tag with songs they do
like. The fix is to reduce the influence of any single categorical feature — which is
exactly what the weight-shift experiment demonstrated.
