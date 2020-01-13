import requests, json, re

def find_wirehouse(name, number):
    data = {
        "modelName": "AddressGeneral",
        "calledMethod": "getWarehouses",

        "methodProperties": {
            "CityName": name,
            "Language": "ru",
        },
        "apiKey": "<new postal key>"
    }
    response = requests.post("https://api.novaposhta.ua/v2.0/json/", json=data)
    wirehouses = json.loads(response.text)["data"]
    for wirehouse in wirehouses:
        result = re.match(r'Отделение №{}'.format(number), wirehouse["DescriptionRu"])
        if result != None:
            data = {"ref":wirehouse["Ref"], "title":wirehouse["DescriptionRu"]}

            return data
    return None
