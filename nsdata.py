import nightscout
from datetime import timedelta, datetime
from pprint import pprint
import operator
import pytz

utc = pytz.UTC


def seconds_midnight(time):
    midnight = time.replace(hour=0, minute=0, second=0, microsecond=0)
    seconds = (time - midnight).seconds
    return seconds


def get_timeslot_index(timeAsSeconds, time_slot):
    # print(timeAsSeconds)
    index = 0
    for o in range(len(time_slot) - 1):
        if timeAsSeconds >= time_slot[index] and timeAsSeconds <= time_slot[index + 1]:
            return index + 1
        else:
            index = index + 1

    return 0


def convert_basal_list(basal_changes_list):
    return_dict = []

    temp = []
    current_date = utc.localize(datetime.now())
    for change in basal_changes_list:
        temp.append(
            {
                "date": change["date"],
                "timeAsSeconds": seconds_midnight(change["date"]),
                "rate": change["rate"],
                "duration": change["duration"] * 60,
                "treat": change["treat"],
            }
        )
        if change["date"].date() != current_date.date():
            current_date = change["date"]
            return_dict.append(temp)
            temp = []

    return return_dict


def calculated_basal(api, date, basal_change_list):
    profiles = api.get_profiles()
    profile = profiles.get_profile_definition_active_at(utc.localize(date))

    profil = profile._json["defaultProfile"]
    basal_schedule = profile._json["store"][profil]["basal"]
    # print(basal_schedule)
    insulin_per_hour = []
    time_slot = []
    total_programmed_basal = 0
    for i in range(len(basal_schedule)):
        insulin_per_hour.append(basal_schedule[i]["value"])
        time_slot.append(basal_schedule[i]["timeAsSeconds"])
    time_slot.remove(0)
    time_slot.append(86400)

    daily_basal = []
    for i in range(len(insulin_per_hour)):
        if i == 0:
            total_programmed_basal = insulin_per_hour[i] * time_slot[i] / 60 / 60
        else:
            total_programmed_basal += insulin_per_hour[i] * (
                (time_slot[i] / 60 / 60) - (time_slot[i - 1] / 60 / 60)
            )

    for change in basal_change_list:
        changes = []
        for item in change:
            timeAsSeconds = item["timeAsSeconds"]
            item_rate = item["rate"]
            item_duration = item["duration"]

            index = 0
            insulin_per_hour_ = 0

            index = get_timeslot_index(timeAsSeconds, time_slot)
            # print(index)
            insulin_per_hour_ = insulin_per_hour[index]

            if item_rate == 0:
                changes.append((insulin_per_hour_ * item_duration / 60 / 60 * -1))
            elif insulin_per_hour_ > item_rate:
                changes.append((item_rate * item_duration / 60 / 60 * -1))

            elif insulin_per_hour_ < item_rate:
                changes.append((item_rate * item_duration / 60 / 60))

        daily_basal.append(
            {
                "pgm": total_programmed_basal,
                "change": sum(changes),
                "date": change[0]["date"].replace(hour=12, minute=00, second=00),
            }
        )

    # print(daily_basal)
    return daily_basal


def nsdata(adress: str, date_string: str, days: int, apisecret: str):

    count = int(days) * 288

    date_time = datetime.strptime(date_string, "%Y-%m-%d") + timedelta(days=1)

    min_date = datetime.strftime(date_time - timedelta(days=int(days)), "%Y-%m-%d")
    max_date = datetime.strftime(date_time, "%Y-%m-%d")

    api = nightscout.Api(adress, api_secret=apisecret.encode("utf-8"))
    entries = api.get_sgvs(
        {
            "find[dateString][$gte]": min_date,
            "find[dateString][$lte]": max_date,
            "count": count,
        }
    )

    treatments = api.get_treatments(
        {
            "find[created_at][$gte]": min_date,
            "find[created_at][$lte]": max_date,
            "count": 20000,
        }
    )

    json = []
    basal_change_list = []

    for entry in entries:
        sgv = round(entry.sgv / 18, 1)
        json.append({"sgv": sgv, "date": entry.date})

    for treat in treatments:
        if treat.timestamp is not None:  # type: ignore
            if treat.insulin is not None:  # type: ignore
                json.append({"insulin": treat.insulin, "date": treat.timestamp})  # type: ignore
            if treat.carbs is not None:  # type: ignore
                json.append({"carbs": treat.carbs, "date": treat.timestamp})  # type: ignore

    #         if treat.eventType is not None and treat.eventType == "Temp Basal":  # type: ignore
    #             basal_change_list.append(
    #                 {
    #                     "date": treat.timestamp,
    #                     "rate": treat.rate,
    #                     "duration": treat.duration,
    #                     "treat": treat,
    #                 }
    #             )
    # basal_change_list = convert_basal_list(basal_change_list)
    # calc_basal = calculated_basal(api, date_time, basal_change_list)
    # for basal in calc_basal:
    #     total = 0
    #     total = basal["pgm"] + basal["change"]
    #     json.append({"basal": round(total,2), "date": basal["date"]})
    # json.sort(key=operator.itemgetter("date"))

    return json


if __name__ == "__main__":
    print(get_timeslot_index(6000, [0, 2000, 4000, 5000, 6000]))
