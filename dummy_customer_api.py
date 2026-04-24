# file: dummy_customer_api.py
from flask import Flask, request, jsonify
import random

app = Flask(__name__)

# simulate messy unstructured text responses
ORDERS = [
    "Order 1001: Buyer=John Davis, Location=Columbus, OH, Total=$899.99, Items: laptop",
    "Order 1002: Buyer=Sarah Liu, Location=Austin, TX, Total=$162.50, Items: headphones",
    "Order 1003: Buyer=Mike Turner, Location=Cleveland, OH, Total=$1349.00, Items: gaming pc",
    "Order 1004: Buyer=Rachel Kim, Location=Seattle, WA, Total=$92.50, Items: coffee maker",
    "Order 1005: Buyer=Chris Myers, Location=Cincinnati, OH, Total=$389.00, Items: monitor",
    "Buyer=Adam Smith, Location=New York, NY, Total=$58.00, Items: desk lamp, Order 1006",
    "Total=$165.00, Items: headphones, Order 1007: Buyer=Jary Tolentino, Location=Arlington, VA",
    "Location=Los Angeles, CA, Total=$875.00, Items: laptop, Order 1008: Buyer=Maya Singh",
    "Location=Seattle, WA, Total=$45.00, Items: mouse, Order 1009: Buyer=Emily Chen",
    "Total=$22.50, Items: hdmi cable, Order 1010: Buyer=Marcus Webb, Location=Austin, TX",
    "Order 1011: Buyer=Priya Nair, Location=New York, NY, Total=$72.00, Items: earphones",
    "Order 1012: Buyer=Tom Nguyen, Location=Columbus, OH, Total=$78.00, Items: keyboard",
    "Order 1013: Buyer=Lisa Park, Location=Los Angeles, CA, Total=$410.00, Items: monitor",
    "Location=Cleveland, OH, Total=$1425.00, Items: gaming pc, Order 1014: Buyer=Derek Hall",
    "Buyer=Nina Patel, Location=Seattle, WA, Total=$105.00, Items: coffee maker, Order 1015",
    "Buyer=Carlos Rivera, Location=Austin, TX, Total=$917.00, Items: laptop, mouse, Order 1016",
    "Order 1017: Buyer=Fiona Grant, Location=New York, NY, Total=$878.00, Items: laptop, headphones",
    "Buyer=James Wu, Location=Cincinnati, OH, Items: coffee maker, desk lamp, Total=$148.00, Order 1018",
    "Order 1019: Buyer=Aisha Moore, Location=Los Angeles, CA, Total=$98.00, Items: hdmi cable, mouse",
    "Order 1020: Buyer=Ryan Scott, Location=Columbus, OH, Total=$1395.00, Items: gaming pc, mouse",
    "Order 1021: Buyer=Hannah Brooks, Location=Seattle, WA, Total=$252.00, Items: headphones, coffee maker",
    "Location=Arlington, VA, Buyer=Kevin Tran, Order 1022, Items: monitor, keyboard Total=$475.00",
    "Order 1023: Buyer=Olivia Stone, Location=Austin, TX, Total=$920.00, Items: laptop, earphones",
    "Order 1024: Buyer=Daniel Fox, Location=Cleveland, OH, Total=$422.00, Items: monitor, hdmi cable",
    "Order 1025, Buyer=Mia Santos, Location=New York, NY, Items: gaming pc, keyboard, Total=$1480.00",
    "Order 1026: Buyer=Ethan Cole, Location=Los Angeles, CA, Total=$498.00, Items: monitor, desk lamp",
    "Order 1027: Buyer=Grace Kim, Location=Cincinnati, OH, Total=$168.00, Items: headphones, mouse",
    "Order 1028: Buyer=Aaron Bell, Location=Arlington, VA, Total=$895.00, Items: laptop, hdmi cable",
    "Order 1029: Buyer=Sophia James, Location=Seattle, WA, Total=$218.00, Items: earphones, desk lamp",
    "Location=Austin, TX, Total=$1820.00, Items: gaming pc, monitor, Order 1030: Buyer=Liam Foster",
    "Order 1031: Buyer=Nora Choi, Location=Seattle, WA, Total=$145.00, Items: mouse, keyboard, hdmi cable",
    "Order 1032: Buyer=Victor Reyes, Location=Austin, TX, Total=$1405.00, Items: laptop, monitor, keyboard",
    "Order 1033: Buyer=Peter Graves, Location=Arlington, VA, Total=$190.00, Items: coffee maker, desk lamp, mouse",
    "Order 1034: Buyer=Zoe Baker, Location=New York, NY, Total=$395.00, Items: headphones, earphones, mouse",
    "Order 1035: Buyer=Alex Park, Location=Los Angeles, CA, Total=$1620.00, Items: gaming pc, mouse, hdmi cable",
    "Order 1036: Buyer=Henry Kato, Location=Columbus, OH, Total=$902.00, Items: laptop, keyboard, hdmi cable",
    "Order 1037: Buyer=Clara Dubois, Location=Los Angeles, CA, Total=$243.00, Items: monitor, keyboard, mouse",
    "Order 1038: Buyer=Isaac Walker, Location=New York, NY, Total=$845.00, Items: monitor, headphones, earphones",
    "Order 1039: Buyer=Sunny Patel, Location=Arlington, VA, Total=$945.00, Items: laptop, earphones, mouse",
    "Order 1040: Buyer=Leo Martinez, Location=Columbus, OH, Total=$215.00, Items: coffee maker, desk lamp, hdmi cable",
    "Order 1041: Buyer=Sara Ahmed, Location=Seattle, WA, Total=$338.00, Items: headphones, coffee maker, desk lamp",
    "Order 1042: Buyer=Omar Farouk, Location=Austin, TX, Total=$1510.00, Items: gaming pc, keyboard, mouse",
    "Items: laptop, monitor, headphones, Buyer=Julia Ross, Order 1043, Location=Los Angeles, CA, Total=$1430.00",
    "Order 1044: Buyer=David Chen, Location=New York, NY, Total=$478.00, Items: monitor, mouse, hdmi cable",
    "Order 1045: Buyer=Rebecca Lee, Location=Cleveland, OH, Total=$2235.00, Items: gaming pc, laptop, mouse, hdmi cable",
    "Order 1046: Buyer=Trevor Blake, Location=Arlington, VA, Total=$1185.00, Items: laptop, headphones, mouse, coffee maker",
    "Order 1047: Buyer=Ivy Wang, Location=Cincinnati, OH, Total=$1640.00, Items: gaming pc, headphones, keyboard, desk lamp",
    "Order 1048: Buyer=Marco Silva, Location=Austin, TX, Total=$1358.00, Items: laptop, headphones, mouse, keyboard",
    "Order 1049: Buyer=Eva Johansson, Location=Seattle, WA, Total=$2415.00, Items: gaming pc, laptop, headphones, coffee maker",
    "Order 1050: Buyer=Nathan Cole, Location=New York, NY, Total=$535.00, Items: monitor, headphones, mouse, keyboard",
    "Order 1051: Buyer=Amara Okoye, Location=Los Angeles, CA, Total=$1180.00, Items: monitor, monitor, monitor, mouse",
    "Order 1052: Buyer=Ben Hayes, Location=Columbus, OH, Total=$168.00, Items: hdmi cable, hdmi cable, mouse, keyboard",
    "Order 1053: Buyer=Chloe Webb, Location=Austin, TX, Total=$2290.00, Items: laptop, laptop, monitor, hdmi cable",
    "Order 1054: Buyer=Theo Marshall, Location=Cleveland, OH, Total=$328.00, Items: headphones, earphones, desk lamp, mouse",
    "Order 1055: Buyer=Gabe Fischer, Location=Arlington, VA, Total=$175.00, Items: mouse, mouse, keyboard, hdmi cable",
    "Order 1056: Buyer=Ruby Morgan, Location=Seattle, WA, Total=$225.00, Items: keyboard, keyboard, mouse, hdmi cable, hdmi cable",
    "Order 1057: Buyer=Finn Gallagher, Location=Cincinnati, OH, Total=$285.00, Items: keyboard, keyboard, keyboard, mouse, mouse",
    "Order 1058: Buyer=Lena Ortiz, Location=Los Angeles, CA, Total=$132.00, Items: mouse, mouse, mouse, hdmi cable",
    "Order 1059: Buyer=Reese Palmer, Location=New York, NY, Total=$310.00, Items: keyboard, keyboard, mouse, mouse, hdmi cable",
    "Order 1060: Buyer=Asha Venkat, Location=Austin, TX, Total=$325.00, Items: headphones, headphones",
    "Order 1061: Buyer=Dominic Ross, Location=Columbus, OH, Total=$408.00, Items: headphones, headphones, earphones",
    "Order 1062: Buyer=Yuki Tanaka, Location=Seattle, WA, Total=$560.00, Items: headphones, headphones, earphones, earphones",
    "Order 1063: Buyer=Mateo Flores, Location=Arlington, VA, Total=$245.00, Items: earphones, earphones, earphones",
    "Order 1064: Buyer=Amelia Reid, Location=Cleveland, OH, Total=$485.00, Items: headphones, earphones, earphones, mouse",
    "Order 1065: Buyer=Theo Knight, Location=Cincinnati, OH, Total=$195.00, Items: coffee maker, desk lamp, desk lamp",
    "Order 1066: Buyer=Rosa Hernandez, Location=Los Angeles, CA, Total=$240.00, Items: coffee maker, coffee maker, desk lamp",
    "Order 1067: Buyer=Cole Richards, Location=Austin, TX, Total=$315.00, Items: coffee maker, coffee maker, desk lamp, desk lamp",
    "Order 1068: Buyer=Willow Barnes, Location=Columbus, OH, Total=$180.00, Items: desk lamp, desk lamp, desk lamp",
    "Order 1069: Buyer=Quinn Hayes, Location=Seattle, WA, Total=$270.00, Items: coffee maker, coffee maker, coffee maker",
    "Order 1070: Buyer=Elise Moreau, Location=Los Angeles, CA, Total=$2195.00, Items: laptop, monitor, monitor",
    "Order 1071: Buyer=Sam Brennan, Location=New York, NY, Total=$3050.00, Items: laptop, laptop, monitor",
    "Order 1072: Buyer=Priya Shah, Location=Cleveland, OH, Total=$3725.00, Items: gaming pc, laptop, monitor",
    "Order 1073: Buyer=Noah Kessler, Location=Arlington, VA, Total=$4480.00, Items: gaming pc, laptop, monitor, monitor",
    "Order 1074: Buyer=Iris Chen, Location=Columbus, OH, Total=$2850.00, Items: gaming pc, gaming pc",
    "Order 1075: Buyer=Jaxon Pierce, Location=Seattle, WA, Total=$1680.00, Items: laptop, laptop",
    "Order 1076: Buyer=Piper Fuentes, Location=Austin, TX, Total=$2945.00, Items: laptop, monitor, headphones, mouse, keyboard",
    "Order 1077: Buyer=Roman Scott, Location=Cincinnati, OH, Total=$1850.00, Items: gaming pc, headphones, coffee maker, desk lamp",
    "Order 1078: Buyer=Tessa Cho, Location=Los Angeles, CA, Total=$1395.00, Items: laptop, headphones, coffee maker, hdmi cable",
    "Order 1079: Buyer=Griffin Beck, Location=New York, NY, Total=$2280.00, Items: laptop, monitor, mouse, keyboard, hdmi cable",
    "Order 1080: Buyer=Delilah Shaw, Location=Arlington, VA, Total=$3680.00, Items: gaming pc, laptop, headphones, mouse",
    "Order 1081: Buyer=Xavier Kane, Location=Cleveland, OH, Total=$1545.00, Items: gaming pc, earphones, hdmi cable, desk lamp",
    "Order 1082: Buyer=Juno Vasquez, Location=Columbus, OH, Total=$1080.00, Items: laptop, headphones, mouse, coffee maker",
    "Order 1083: Buyer=Stella Park, Location=Seattle, WA, Total=$2410.00, Items: gaming pc, monitor, mouse, keyboard",
    "Order 1084: Buyer=Oscar Blum, Location=Austin, TX, Total=$28.00, Items: hdmi cable",
    "Order 1085: Buyer=Maren Holt, Location=Los Angeles, CA, Total=$62.00, Items: desk lamp",
    "Buyer=Archer Quinn, Location=Columbus, OH, Items: gaming pc, gaming pc, monitor, Total=$3220.00, Order 1086",
    "Items: headphones, headphones, headphones, Buyer=Nia Rhodes, Order 1087, Location=New York, NY, Total=$495.00",
    "Location=Cleveland, OH, Order 1088, Buyer=Colt Reyes Items: laptop, laptop, laptop Total=$2545.00",
    "Order 1089: Buyer=Esme Lindqvist, Location=Arlington, VA, Total=$82.00, Items: keyboard",
    "Order 1090: Buyer=Bodhi Sterling, Location=Seattle, WA, Total=$895.00, Items: laptop",
    "Buyer=Ava Whittaker, Location=Cincinnati, OH, Total=$1125.00, Items: gaming pc, hdmi cable, Order 1091",
    "Order 1092: Buyer=Remy Calloway, Location=Los Angeles, CA, Total=$428.00, Items: monitor, mouse",
    "Location=Austin, TX, Total=$215.00, Items: headphones, mouse, Order 1093: Buyer=Oak Pemberton",
    "Order 1094: Buyer=Juniper Wells, Location=New York, NY, Total=$158.00, Items: coffee maker, hdmi cable, mouse",
    "Order 1095: Buyer=Silas Montgomery, Location=Columbus, OH, Total=$1975.00, Items: laptop, monitor, headphones",
    "Order 1096: Buyer=Maribel Alonso, Location=Seattle, WA, Total=$1362.00, Items: gaming pc, mouse, hdmi cable, desk lamp",
    "Order 1097: Buyer=Rio Whitfield, Location=Cleveland, OH, Total=$690.00, Items: monitor, headphones, desk lamp",
    "Order 1098: Buyer=Sage Hollister, Location=Arlington, VA, Total=$2140.00, Items: gaming pc, headphones, mouse",
    "Order 1099: Buyer=Basil Moreno, Location=Cincinnati, OH, Total=$1815.00, Items: laptop, monitor, headphones, hdmi cable",
    "Order 1100: Buyer=Wren Callahan, Location=Los Angeles, CA, Total=$3895.00, Items: gaming pc, laptop, headphones, mouse, keyboard",
]

@app.route("/api/orders", methods=["GET"])
def get_orders():
    """
    Returns orders as messy text. In real life, customers
    would have unpredictable formatting. The AI must parse it.
    """
    limit = request.args.get("limit", default=len(ORDERS), type=int)
    sample = random.sample(ORDERS, min(limit, len(ORDERS)))

    return jsonify({
        "status": "ok",
        "raw_orders": sample
    })


@app.route("/api/order/<order_id>", methods=["GET"])
def get_order_by_id(order_id):
    """
    Fetch a single order by scanning the text.
    """
    for text in ORDERS:
        if order_id in text:
            return jsonify({
                "status": "ok",
                "raw_order": text
            })

    return jsonify({"status": "not_found"}), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002
            , debug=True)