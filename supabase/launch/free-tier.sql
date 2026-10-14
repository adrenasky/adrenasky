-- Adrenasky launch day: switch on the free tier.
-- Run ONCE on launch day, after Paystack is live. Until then everything stays free for testers.
-- Free after the trial: the first 5 questions in every chapter, and the notes for each subject's first 2 chapters.
-- Everything else needs a trial or a paid plan (checked by has_access()).

-- 1. Questions: first 5 per chapter (by question number) stay free.
update public.questions q set is_free = (r.rn <= 5)
from (select id, row_number() over (partition by topic_id order by id) rn from public.questions) r
where r.id = q.id;

-- 2. Notes: the first 2 chapters of each subject stay free.
update public.notes n set is_free = (r.rn <= 2)
from (select t.id, row_number() over (partition by t.subject_id order by t.sort_order, t.id) rn from public.topics t) r
where r.id = n.topic_id;

-- 3. Founding members must claim their price within 30 days of launch.
update public.profiles set founding_claim_by = now() + interval '30 days' where is_founding;

-- Check: free questions per subject and free note chapters.
select t.subject_id, count(*) filter (where q.is_free) free_q, count(*) total_q
from public.questions q join public.topics t on t.id = q.topic_id group by 1 order by 1;
