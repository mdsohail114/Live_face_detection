h, m = map(int, time_str.split(":"))

digits = [int(time_str[0]), int(time_str[1]),
          int(time_str[3]), int(time_str[4])]

candidates = []

for hh in range(1, 13):
    for mm in range(60):
        candidate = f"{hh:02d}:{mm:02d}"

        if candidate == time_str:
            continue

        cand_digits = [int(candidate[0]), int(candidate[1]),
                       int(candidate[3]), int(candidate[4])]

        differences = 0

        for i in range(4):
            if digits[i] != cand_digits[i]:
                if one_segment_difference(digits[i], cand_digits[i]):
                    differences += 1
                else:
                    differences = 100
                    break

        if differences != 1:
            continue

        hour_diff = abs(hh - h)
        hour_diff = min(hour_diff, 12 - hour_diff)

        minute_diff = abs(mm - m)
        minute_diff = min(minute_diff, 60 - minute_diff)

        cost = hour_diff * 60 * X + minute_diff * Y

        candidates.append((cost, candidate))

if not candidates:
    print("No closest valid time possible")
else:
    candidates.sort()
    print(candidates[0][1])