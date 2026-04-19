# file: dummy_customer_api.py
from flask import Flask, request, jsonify
import random

app = Flask(__name__)

# simulate messy unstructured text responses
ORDERS = [
    "Order 1001: Buyer=John Davis, Location=Columbus, OH, Total=$742.10, Items: laptop, hdmi cable",
    "Order 1002: Buyer=Sarah Liu, Location=Austin, TX, Total=$156.55, Items: headphones",
    "Order 1003: Buyer=Mike Turner, Location=Cleveland, OH, Total=$1299.99, Items: gaming pc, mouse",
    "Order 1004: Buyer=Rachel Kim, Location=Seattle, WA, Total=$89.50, Items: coffee maker",
    "Order 1005: Buyer=Chris Myers, Location=Cincinnati, OH, Total=$512.00, Items: monitor, desk lamp",
    "Order 1006: Location=New York, NY, Buyer=Adam Smith, Items: monitor, desk lamp, Total=$52.00",
    "Location=Arlington, VA, Buyer=Jary Tolentino, Items: headphones Total=$160.00, Order 1007",
    "Location=Los Angeles, CA, Order 1008, Buyer=Jary Tolentino Items: laptop Total=$899.99",
    "Order 1009: Buyer=Emily Chen, Location=Seattle, WA, Total=$1149.99, Items: laptop, mouse",
    "Order 1010: Buyer=Marcus Webb, Location=Austin, TX, Total=$374.00, Items: monitor, hdmi cable",
    "Order 1011: Buyer=Priya Nair, Location=New York, NY, Total=$229.99, Items: headphones, desk lamp",
    "Order 1012: Buyer=Tom Nguyen, Location=Columbus, OH, Total=$849.50, Items: laptop, coffee maker",
    "Items: gaming pc, monitor, Buyer=Lisa Park, Order 1013, Location=Los Angeles, CA, Total=$1899.00",
    "Order 1014: Buyer=Derek Hall, Location=Cleveland, OH, Total=$44.99, Items: hdmi cable, earphones",
    "Location=Seattle, WA, Order 1015, Buyer=Nina Patel, Total=$512.75, Items: monitor, mouse",
    "Order 1016: Buyer=Carlos Rivera, Location=Austin, TX, Total=$999.99, Items: gaming pc, headphones",
    "Order 1017: Buyer=Fiona Grant, Location=New York, NY, Total=$1450.00, Items: laptop, monitor",
    "Buyer=James Wu, Location=Cincinnati, OH, Items: coffee maker, desk lamp, Total=$118.30, Order 1018",
    "Order 1019: Buyer=Aisha Moore, Location=Los Angeles, CA, Total=$67.45, Items: hdmi cable, earphones",
    "Order 1020: Buyer=Ryan Scott, Location=Columbus, OH, Total=$1599.99, Items: gaming pc, mouse, hdmi cable",
    "Order 1021: Buyer=Hannah Brooks, Location=Seattle, WA, Total=$189.00, Items: headphones, coffee maker",
    "Location=Arlington, VA, Buyer=Kevin Tran, Order 1022, Items: monitor Total=$389.99",
    "Order 1023: Buyer=Olivia Stone, Location=Austin, TX, Total=$754.20, Items: laptop, earphones",
    "Order 1024: Buyer=Daniel Fox, Location=Cleveland, OH, Total=$299.99, Items: monitor, hdmi cable",
    "Order 1025, Buyer=Mia Santos, Location=New York, NY, Items: gaming pc, keyboard, Total=$1749.00",
    "Order 1026: Buyer=Ethan Cole, Location=Los Angeles, CA, Total=$432.00, Items: monitor, desk lamp, mouse",
    "Buyer=Grace Kim, Order 1027, Location=Cincinnati, OH, Total=$88.00, Items: coffee maker",
    "Order 1028: Buyer=Aaron Bell, Location=Arlington, VA, Total=$1099.00, Items: laptop, hdmi cable, mouse",
    "Order 1029: Buyer=Sophia James, Location=Seattle, WA, Total=$349.99, Items: headphones, desk lamp",
    "Order 1030: Buyer=Liam Foster, Location=Austin, TX, Total=$2199.99, Items: gaming pc, monitor, mouse, keyboard",
    "Order 1031: Buyer=John Smith, Location=Columbus, OH, Total=$3190.10, Items: laptop, laptop, hdmi cable",
    "Order 1032: Buyer=Andrew Smith, Location=Columbus, OH, Total=$5402.00, Items: gaming pc, laptop, monitor, hdmi cable",
    "Order 1033: Buyer=Nora Choi, Location=Seattle, WA, Total=$142.50, Items: mouse, keyboard, hdmi cable",
    "Order 1034: Buyer=Victor Reyes, Location=Austin, TX, Total=$198.75, Items: mouse, mouse, keyboard, hdmi cable",
    "Order 1035: Buyer=Peter Graves, Location=Arlington, VA, Total=$245.00, Items: keyboard, keyboard, mouse, hdmi cable, hdmi cable",
    "Order 1036: Buyer=Zoe Baker, Location=New York, NY, Total=$380.00, Items: headphones, headphones",
    "Order 1037: Buyer=Alex Park, Location=Los Angeles, CA, Total=$495.50, Items: headphones, headphones, earphones",
    "Order 1038: Buyer=Maya Singh, Location=Cincinnati, OH, Total=$620.00, Items: headphones, headphones, earphones, earphones",
    "Order 1039: Buyer=Leo Martinez, Location=Columbus, OH, Total=$185.00, Items: coffee maker, desk lamp, desk lamp",
    "Order 1040: Buyer=Sara Ahmed, Location=Seattle, WA, Total=$245.50, Items: coffee maker, coffee maker, desk lamp",
    "Order 1041: Buyer=Omar Farouk, Location=Austin, TX, Total=$330.00, Items: coffee maker, coffee maker, desk lamp, desk lamp",
    "Order 1042: Buyer=Julia Ross, Location=Los Angeles, CA, Total=$2350.00, Items: laptop, monitor, monitor",
    "Order 1043: Buyer=David Chen, Location=New York, NY, Total=$3100.00, Items: laptop, laptop, monitor",
    "Order 1044: Buyer=Rebecca Lee, Location=Cleveland, OH, Total=$4250.00, Items: gaming pc, laptop, monitor, monitor",
    "Order 1045: Buyer=Trevor Blake, Location=Arlington, VA, Total=$1180.00, Items: laptop, headphones, mouse, coffee maker",
    "Order 1046: Buyer=Ivy Wang, Location=Cincinnati, OH, Total=$1920.50, Items: gaming pc, headphones, keyboard, desk lamp",
    "Order 1047: Buyer=Marco Silva, Location=Austin, TX, Total=$2680.00, Items: laptop, monitor, headphones, mouse, keyboard",
    "Order 1048: Buyer=Eva Johansson, Location=Seattle, WA, Total=$3950.00, Items: gaming pc, laptop, headphones, coffee maker",
    "Order 1049: Buyer=Henry Kato, Location=Columbus, OH, Total=$165.50, Items: hdmi cable, hdmi cable, hdmi cable, mouse, keyboard",
    "Order 1050: Buyer=Clara Dubois, Location=Los Angeles, CA, Total=$285.00, Items: keyboard, keyboard, keyboard, mouse, mouse",
    "Order 1051: Buyer=Isaac Walker, Location=New York, NY, Total=$850.00, Items: monitor, headphones, headphones, earphones",
    "Order 1052: Buyer=Sunny Patel, Location=Arlington, VA, Total=$1050.50, Items: laptop, earphones, earphones, mouse"
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
    app.run(host="0.0.0.0", port=5001, debug=True)