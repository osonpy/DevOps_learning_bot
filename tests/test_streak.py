from datetime import date, timedelta

from src.services import progress, srs, streak

SUN = 6
MON = date(2026, 10, 12)  # Dushanba


def d(offset: int) -> date:
    return MON + timedelta(days=offset)


def test_no_missed_consecutive_days():
    assert streak.missed_days_between(d(0), d(1), SUN) == 0


def test_missed_counts_only_required_days():
    # Shanba bajarildi -> Yakshanba (dam) o'tkazildi -> Dushanba: 0 missed
    assert streak.missed_days_between(d(5), d(7), SUN) == 0
    # Juma bajarildi -> Shanba o'tkazildi, Yakshanba dam -> Dushanba: 1 missed
    assert streak.missed_days_between(d(4), d(7), SUN) == 1


def test_apply_completion_increments_and_resets():
    started = d(0)
    u = streak.apply_completion(0, 0, None, started, d(0), SUN)
    assert (u.streak, u.best_streak, u.counted) == (1, 1, True)
    u = streak.apply_completion(1, 1, d(0), started, d(1), SUN)
    assert u.streak == 2
    # 2 kun o'tkazib yuborildi -> streak 1 dan qayta
    u = streak.apply_completion(2, 2, d(1), started, d(4), SUN)
    assert (u.streak, u.best_streak) == (1, 2)


def test_same_day_not_counted_twice():
    u = streak.apply_completion(3, 3, d(2), d(0), d(2), SUN)
    assert (u.streak, u.counted) == (3, False)


def test_rest_day_keeps_streak():
    # Shanba -> Dushanba (Yakshanba dam olish)
    u = streak.apply_completion(6, 6, d(5), d(0), d(7), SUN)
    assert u.streak == 7


def test_penalty_kind_thresholds():
    assert streak.penalty_kind(2, 3, 5) is None
    assert streak.penalty_kind(3, 3, 5) == "quiz"
    assert streak.penalty_kind(6, 3, 5) == "hardcore"


def test_progress_bar_and_levels():
    assert progress.bar(5, 10, 10) == "▰▰▰▰▰▱▱▱▱▱ 50%"
    assert progress.level_for(0)[0].endswith("Intern")
    name, left = progress.level_for(120)
    assert "Padawan" in name and left == 130


def test_srs_intervals_and_mastery():
    today = d(0)
    box, lapses, due = 0, 0, srs.first_due(today)
    assert due == d(1)
    seen = []
    for _ in range(5):
        st = srs.answer(box, lapses, True, today)
        box, lapses = st.box, st.lapses
        seen.append(st.due_date)
    assert seen[:4] == [d(3), d(7), d(21), d(60)]
    assert seen[4] is None and box == srs.MASTERED
    st = srs.answer(3, 0, False, today)
    assert (st.box, st.due_date, st.lapses) == (0, d(1), 1)


def test_week_strip_marks():
    strip = progress.week_strip(d(3), {d(0), d(1)}, SUN, d(0))
    first_line = strip.split("\n")[0].split(" ")
    assert first_line[:4] == ["✅", "✅", "❌", "🔵"]
    assert first_line[6] == "⬜"
