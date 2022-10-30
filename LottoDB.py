import json
import requests
import datetime


class LottoDB:

    def __init__(self):
        self.numbers = []
        self.updated = False
        pass

    def LoadNumbersJSON(self):
        filename = './numbers.json'
        with open(filename, 'r') as handle:
            file_data = json.load(handle)
            for list_to_add in file_data:
                self.numbers.append(list_to_add)
            print('nums', self.numbers)

    def SaveNumbersJSON(self):
        filename = './numbers.json'
        with open(filename, 'w') as handle:
            handle.write('[')
            mline = len(self.numbers)-1
            for i in range(mline):
                num_to_json = json.dumps(self.numbers[i])
                handle.write(num_to_json + ',\n')
            num_to_json = json.dumps(self.numbers[mline])
            handle.write(num_to_json + ']')      

    def _get_lotto_number_by_draw(self, round_number):
        url = 'https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={}'
        url = url.format(round_number)
        req_result = requests.get(url)
        json_result = req_result.json()
        print(json_result)
        draw_date = json_result.get('drwNoDate', None)
        no_1 = json_result.get('drwtNo1', None)
        no_2 = json_result.get('drwtNo2', None)
        no_3 = json_result.get('drwtNo3', None)
        no_4 = json_result.get('drwtNo4', None)
        no_5 = json_result.get('drwtNo5', None)
        no_6 = json_result.get('drwtNo6', None)
        no_bonus = json_result.get('bnusNo', None)
        to_save = { 'draw': round_number, 'date': draw_date, 'n': [no_1,no_2,no_3,no_4,no_5,no_6], 'bonus': no_bonus }
        return to_save

    def CheckUpdate(self):
        ''' require LoadNumbersJSON first '''
        today = datetime.datetime.today()
        date_saved = datetime.datetime.strptime(self.numbers[-1]['date'], "%Y-%m-%d")
        date_to_be_saved = date_saved + datetime.timedelta(days=7, hours=23)
        while (today > date_to_be_saved):
            new_draw_num = self.numbers[-1]['draw'] + 1
            new_set = self._get_lotto_number_by_draw(new_draw_num)
            self.numbers.append(new_set)
            self.updated = True
            date_to_be_saved = date_to_be_saved + datetime.timedelta(days=7)
        if self.updated:
            print("writing updated numbers...")
            self.SaveNumbersJSON()
        else:
            print("...already up to date numbers")
        return self.updated
