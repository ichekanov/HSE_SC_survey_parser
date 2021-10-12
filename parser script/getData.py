import csv
import requests
from time import sleep
import vk
from progress.bar import IncrementalBar
# from private_data import VK_personal_token
VK_personal_token = "YOUR TOKEN"


def get_polls(owner_id, max_date):
    ID = []
    k = 0
    url = f"https://api.vk.com/method/wall.get?owner_id={owner_id}&access_token={VK_personal_token}&v=5.131"
    req = requests.get(
        url, params={'owner_id': owner_id, 'count': 100, 'offset': k})
    src = req.json()
    mx = src["response"]["count"]
    print(f"Number of posts: {mx}")
    bar = IncrementalBar('Posts', max=mx)
    while k < mx and src["response"]["items"][0]["date"] > max_date:
        sleep(0.4)
        req = requests.get(url, params={'owner_id': owner_id, 'offset': k})
        src = req.json()
        posts = src["response"]["items"]
        for post in posts:
            if "attachments" in post:
                for x in post["attachments"]:
                    if "poll" in x:
                        ID.append((x["poll"]["id"], x["poll"]["question"]))
            k += 1
            bar.next()
        # print(f" {k}")
    bar.finish()
    print("Done parsing!\n")
    return ID  # [(vote_id, vote_name), ...]


def get_poll_results(poll_id, owner_id):
    def get_poll_data():
        sleep(0.4)
        poll_data = api.polls.getById(poll_id=poll_id, owner_id=owner_id)
        return poll_data

    def get_voters():
        sleep(0.4)
        try:
            votes = api.polls.getVoters(poll_id=poll_id, answer_ids=variants)
            return votes
        except Exception as e:
            if "Access denied, please vote first." in str(e):
                return False
            else:
                raise e

    def vote():
        sleep(0.5)
        done = False
        captcha = False
        text = ""
        captcha_sid = ""
        while not done:
            if not captcha:
                url = f"https://api.vk.com/method/polls.addVote?owner_id={owner_id}&poll_id={poll_id}&answer_ids={variants[-1]}&access_token={VK_personal_token}&v=5.131"
                req = requests.get(url)
                ans = req.json()
            else:
                url = f"https://api.vk.com/method/polls.addVote?owner_id={owner_id}&poll_id={poll_id}&answer_ids={variants[-1]}&access_token={VK_personal_token}&captcha_sid={captcha_sid}&captcha_key={text}&v=5.131"
                req = requests.get(url)
                ans = req.json()
            if 'response' in ans:
                print(f"Voted in {poll_id} for {variants_with_names[-1][1]}")
                done = True
                sleep(0.5)
            else:
                try:
                    captcha_sid = ans['error']['captcha_sid']
                    print(ans['error']['captcha_img'])
                    text = input("Input captcha: ")
                    captcha = True
                except:
                    print(ans)

    poll_data = get_poll_data()
    variants = [x['id'] for x in poll_data['answers']]
    variants_with_names = [(x['id'], x['text']) for x in poll_data['answers']]
    votes = get_voters()
    if not votes:
        vote()
        votes = get_voters()
    # print(poll_data)
    # print(variants)
    # print(variants_with_names)
    # print(votes)
    users_by_variants = {}
    for k in range(len(variants_with_names)):
        users_by_variants[variants_with_names[k]
                          ] = votes[k]['users']['items']
    return users_by_variants  # {(variant_id, variant_name): [voters], ...}


def get_names(ids):
    # max number of requested users - 1000
    sleep(0.4)
    names = sorted([(x['last_name'], x['first_name'], x['id'])
                    for x in api.users.get(user_ids=ids)])
    return names  # [(last_name, first_name, id), ...]


def write_to_csv(data, path="output.csv"):
    ids = [x[2] for x in voters]
    with open(path, "w", newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file, delimiter=',')
        writer.writerow(['', ''] + [x[0]+" "+x[1] for x in voters])
        for k in data:
            # k = ((poll_id, poll_name), (var_id, var_name)): [voters]
            row = [k[0][1], k[1][1]]
            row += [1 if x in data[k] else 0 for x in ids]
            writer.writerow(row)


def compose_all(group_id, max_date):
    polls = get_polls(group_id, max_date)  # (poll_id, poll_name)
    voters_ids = set()  # IDs of voters
    table = dict()
    for poll in polls:
        # ID for each variant
        answers = get_poll_results(poll[0], group_id)
        results = list(answers.values())
        answers = list(answers)  # IDs and names of variants
        for i in range(len(results)):
            for x in results[i]:
                voters_ids.add(x)  # adding voters
        for i, var in enumerate(answers):
            table[(poll, var)] = results[i]
        print(f"Successfully fetched {poll[1]}!\n")
    global voters
    voters = sorted(get_names(list(voters_ids)))  # names and IDs of voters
    return table  # {((poll_id, poll_name), (var_id, var_name)): [voters], ...}


def main():
    # group_id = "-206802048"  # тестовая группа
    # group_id = "-207790088" # тестовая группа 2
    group_id = "-90904335"  # группа СС
    max_date = 1609459200  # самая ранняя дата, за которую надо получить данные
    write_to_csv(compose_all(group_id, max_date))


if __name__ == "__main__":
    session = vk.Session(access_token=VK_personal_token)
    api = vk.API(session, v='5.131', lang='ru')
    voters = []
    main()
