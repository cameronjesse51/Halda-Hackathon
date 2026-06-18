create or replace function public.peer_college_interest_counts(
  current_student_id uuid,
  current_high_school text,
  requested_college_ids text[]
)
returns table (college_id text, peer_count bigint)
language sql
stable
security definer
set search_path = public, pg_temp
as $$
  select
    recommendation->>'college_id' as college_id,
    count(distinct recommendation_set.student_id) as peer_count
  from public.college_recommendation_sets as recommendation_set
  join public.student_profiles as student
    on student.student_id = recommendation_set.student_id
  cross join lateral jsonb_array_elements(recommendation_set.recommendations) as recommendation
  where recommendation_set.student_id <> current_student_id
    and nullif(btrim(current_high_school), '') is not null
    and lower(btrim(student.high_school)) = lower(btrim(current_high_school))
    and recommendation->>'college_id' = any(requested_college_ids)
  group by recommendation->>'college_id';
$$;

revoke all on function public.peer_college_interest_counts(uuid, text, text[]) from public;
revoke all on function public.peer_college_interest_counts(uuid, text, text[]) from anon, authenticated;
grant execute on function public.peer_college_interest_counts(uuid, text, text[]) to service_role;
