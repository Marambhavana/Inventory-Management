import datetime
import os
import re

from flask import Flask, session, request, render_template, sessions, redirect

import pymongo
from bson import ObjectId

myClient = pymongo.MongoClient('mongodb://localhost:27017/')
mydb = myClient["InventoryManagementSystem"]
owner_col = mydb["Owner"]
category_col = mydb["Categories"]
sub_category_col = mydb["SubCategories"]
product_col = mydb["Products"]
# stock_manager_col = mydb["StockManager"]
sales_person_col = mydb["SalesPerson"]
invoice_col = mydb["Invoices"]
invoice_item_col = mydb["InvoiceItems"]
# supplier_col = mydb["Supplier"]
customer_col = mydb["Customer"]

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
APP_ROOT = APP_ROOT + "/static"

app = Flask(__name__)
app.secret_key = 'inventory'



if owner_col.count_documents({}) == 0:
    query = {"Username": "owner", "password": "owner"}
    owner_col.insert_one(query)


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/oLogin")
def oLogin():
    return render_template("oLogin.html")


@app.route("/smLogin")
def smLogin():
    return render_template("smLogin.html")

@app.route("/spLogin")
def spLogin():
    return render_template("spLogin.html")


@app.route("/oLogin1", methods=['post'])
def oLogin1():
    Username = request.form.get("Username")
    password = request.form.get("password")
    query = {"Username":Username,"password":password}
    count = owner_col.count_documents(query)
    print(count)
    if count > 0:
        print("hii")
        session['role'] = 'owner'
        return redirect("/owner")
    else:
        return render_template("message.html", msg="Invalid Login Details",color='text-danger')




@app.route("/owner")
def owner():
    return render_template("owner.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/addCategory")
def addCategory():
    return render_template("addCategory.html")

@app.route("/addCategory1" ,methods=['post'])
def addCategory1():
    category_name = request.form.get("category_name")
    count = category_col.count_documents({"category_name":category_name})
    if count == 0:
        category_col.insert_one({"category_name":category_name})
        return redirect("/viewCategories")
    else:
        return render_template("message.html",msg='Category ('+category_name+') Already Added',color='text-warning')


@app.route("/viewCategories")
def viewCategories():
    categories = category_col.find()
    return render_template("viewCategories.html",categories=categories)


@app.route("/add_sub_Category")
def add_sub_Category():
    categories = category_col.find()
    return render_template("add_sub_Category.html",categories=categories)

@app.route("/addSubCategory1",methods=['post'])
def addSubCategory1():
    sub_category_name = request.form.get("sub_category_name")
    category_id = request.form.get("category_id")
    sub_category_col.insert_one({"sub_category_name": sub_category_name,"category_id": ObjectId(category_id)})
    return redirect("/view_sub_Categories")


@app.route("/view_sub_Categories")
def view_sub_Categories():
    sub_categories = sub_category_col.find()
    categories = category_col.find()
    return render_template("view_sub_Categories.html",categories=categories,sub_categories=sub_categories,get_category_by_ID=get_category_by_ID)


def get_category_by_ID(category_id):
    category = category_col.find_one({"_id":ObjectId(category_id)})
    return category


@app.route("/addProduct")
def addProduct():
    sub_categories = sub_category_col.find()
    return render_template("addProduct.html",sub_categories=sub_categories)

@app.route("/addProduct1", methods=['post'])
def addProduct1():
    product_name = request.form.get("product_name")
    price = request.form.get("price")
    product_quantity = request.form.get("product_quantity")
    threshold_quantity = request.form.get("threshold_quantity")
    sub_category_id = request.form.get("sub_category_id")
    product_image = request.files.get("product_image")
    path = APP_ROOT + "/ProductImages/" + product_image.filename
    product_image.save(path)
    product_description = request.form.get("product_description")
    product_col.insert_one({"product_name":product_name,"price":price,"product_quantity":product_quantity,"threshold_quantity":threshold_quantity,"product_image":product_image.filename,"product_description":product_description,"sub_category_id":ObjectId(sub_category_id),"product_status":'Available'})
    return render_template("message.html",msg='Product Added',color='text-success')


@app.route("/viewProducts")
def viewProducts():
    category_id = request.args.get("category_id")
    sub_category_id = request.args.get("sub_category_id")
    product_name = request.args.get("product_name")
    if product_name == None:
        product_name = ""
    if category_id == None:
        category_id = "all"
    if sub_category_id == None:
        sub_category_id = "all"
    query = {}
    if session['role'] == 'owner':
        if category_id == 'all' and sub_category_id == 'all' and product_name == '':
            query = {}
        if category_id == 'all' and sub_category_id == 'all' and product_name != '':
            rgx = re.compile(".*" + product_name + ".*", re.IGNORECASE)
            query = {"product_name": rgx}
        elif category_id == 'all' and sub_category_id != 'all' and product_name == '':
            query = {"sub_category_id": ObjectId(sub_category_id)}
        elif category_id == 'all' and sub_category_id != 'all' and product_name != '':
            rgx = re.compile(".*" + product_name + ".*", re.IGNORECASE)
            query = {"sub_category_id": ObjectId(sub_category_id), "product_name": rgx}
        elif category_id != 'all' and sub_category_id == 'all' and product_name == '':
            query2 = {"category_id": ObjectId(category_id)}
            sub_categoires = sub_category_col.find(query2)
            sub_categoires_ids = []
            for sub_categoy in sub_categoires:
                sub_categoires_ids.append({"sub_category_id": sub_categoy['_id']})
            query = {"$or": sub_categoires_ids}
        elif category_id != 'all' and sub_category_id == 'all' and product_name != '':
            query2 = {"category_id": ObjectId(category_id)}
            sub_categoires = sub_category_col.find(query2)
            sub_categoires_ids2 = []
            for sub_category in sub_categoires:
                sub_categoires_ids2.append({"category_id": ObjectId(sub_category['_id'])})
            rgx = re.compile(".*" + product_name + ".*", re.IGNORECASE)
            query = {"$or": sub_categoires_ids2, "product_name": rgx}
        elif category_id != 'all' and sub_category_id != 'all' and product_name == '':
            query = {"sub_category_id": ObjectId(sub_category_id)}
        elif category_id != 'all' and sub_category_id != 'all' and product_name != '':
            rgx = re.compile(".*" + product_name + ".*", re.IGNORECASE)
            query = {"sub_category_id": ObjectId(sub_category_id), "product_name": rgx}
    elif session['role'] == 'stock_manager':
        if category_id == 'all' and sub_category_id == 'all' and product_name == '':
            query = {}
        if category_id == 'all' and sub_category_id == 'all' and product_name != '':
            rgx = re.compile(".*" + product_name + ".*", re.IGNORECASE)
            query = {"product_name": rgx}
        elif category_id == 'all' and sub_category_id != 'all' and product_name == '':
            query = {"sub_category_id": ObjectId(sub_category_id)}
        elif category_id == 'all' and sub_category_id != 'all' and product_name != '':
            rgx = re.compile(".*" + product_name + ".*", re.IGNORECASE)
            query = {"sub_category_id": ObjectId(sub_category_id), "product_name": rgx}
        elif category_id != 'all' and sub_category_id == 'all' and product_name == '':
            query2 = {"category_id": ObjectId(category_id)}
            sub_categoires = sub_category_col.find(query2)
            sub_categoires_ids = []
            for sub_categoy in sub_categoires:
                sub_categoires_ids.append({"sub_category_id": sub_categoy['_id']})
            query = {"$or": sub_categoires_ids}
        elif category_id != 'all' and sub_category_id == 'all' and product_name != '':
            query2 = {"category_id": ObjectId(category_id)}
            sub_categoires = sub_category_col.find(query2)
            sub_categoires_ids2 = []
            for sub_category in sub_categoires:
                sub_categoires_ids2.append({"category_id": ObjectId(sub_category['_id'])})
            rgx = re.compile(".*" + product_name + ".*", re.IGNORECASE)
            query = {"$or": sub_categoires_ids2, "product_name": rgx}
        elif category_id != 'all' and sub_category_id != 'all' and product_name == '':
            query = {"sub_category_id": ObjectId(sub_category_id)}
        elif category_id != 'all' and sub_category_id != 'all' and product_name != '':
            rgx = re.compile(".*" + product_name + ".*", re.IGNORECASE)
            query = {"sub_category_id": ObjectId(sub_category_id), "product_name": rgx}
    elif session['role'] == 'sales_person':
        if category_id == 'all' and sub_category_id == 'all' and product_name == '':
            query = {}
        if category_id == 'all' and sub_category_id == 'all' and product_name != '':
            rgx = re.compile(".*" + product_name + ".*", re.IGNORECASE)
            query = {"product_name": rgx}
        elif category_id == 'all' and sub_category_id != 'all' and product_name == '':
            query = {"sub_category_id": ObjectId(sub_category_id)}
        elif category_id == 'all' and sub_category_id != 'all' and product_name != '':
            rgx = re.compile(".*" + product_name + ".*", re.IGNORECASE)
            query = {"sub_category_id": ObjectId(sub_category_id), "product_name": rgx}
        elif category_id != 'all' and sub_category_id == 'all' and product_name == '':
            query2 = {"category_id": ObjectId(category_id)}
            sub_categoires = sub_category_col.find(query2)
            sub_categoires_ids = []
            for sub_categoy in sub_categoires:
                sub_categoires_ids.append({"sub_category_id": sub_categoy['_id']})
            query = {"$or": sub_categoires_ids}
        elif category_id != 'all' and sub_category_id == 'all' and product_name != '':
            query2 = {"category_id": ObjectId(category_id)}
            sub_categoires = sub_category_col.find(query2)
            sub_categoires_ids2 = []
            for sub_category in sub_categoires:
                sub_categoires_ids2.append({"category_id": ObjectId(sub_category['_id'])})
            rgx = re.compile(".*" + product_name + ".*", re.IGNORECASE)
            query = {"$or": sub_categoires_ids2, "product_name": rgx}
        elif category_id != 'all' and sub_category_id != 'all' and product_name == '':
            query = {"sub_category_id": ObjectId(sub_category_id)}
        elif category_id != 'all' and sub_category_id != 'all' and product_name != '':
            rgx = re.compile(".*" + product_name + ".*", re.IGNORECASE)
            query = {"sub_category_id": ObjectId(sub_category_id), "product_name": rgx}
    products = product_col.find(query)
    categories = category_col.find()
    if category_id != 'all':
        sub_categories = sub_category_col.find({"category_id": ObjectId(category_id)})
    else:
        sub_categories = []
    return render_template("viewProducts.html",sub_category_id=sub_category_id,get_category_by_products=get_category_by_products,get_sub_category_by_products=get_sub_category_by_products,sub_categories=sub_categories,products=products,categories=categories,category_id=category_id,product_name=product_name,str=str)

def get_sub_category_by_products(sub_category_id):
    sub_category = sub_category_col.find_one({"_id":ObjectId(sub_category_id)})
    return sub_category

def get_category_by_products(category_id):
    category = category_col.find_one({"_id":ObjectId(category_id)})
    return category


@app.route("/viewProductDetails")
def viewProductDetails():
    product_id = ObjectId(request.args.get("product_id"))
    product = product_col.find_one({"_id":ObjectId(product_id)})
    return render_template("viewProductDetails.html",product=product,int=int)

@app.route("/editProduct")
def editProduct():
    product_id = ObjectId(request.args.get("product_id"))
    product = product_col.find_one({"_id":ObjectId(product_id)})
    return render_template("editProduct.html",product_id=product_id,product=product)

@app.route("/updateProduct")
def updateProduct():
    product_id = ObjectId(request.args.get("product_id"))
    product = product_col.find_one({"_id": ObjectId(product_id)})
    return render_template("updateProduct.html",product_id=product_id,product=product)


@app.route("/updateProduct1",methods=['post'])
def updateProduct1():
    product_id = ObjectId(request.form.get("product_id"))
    price = request.form.get("price")
    product_quantity = request.form.get("product_quantity")
    threshold_quantity = request.form.get("threshold_quantity")
    query = {"$set": {"price": price, "product_quantity": product_quantity,"threshold_quantity":threshold_quantity}}
    product_col.update_one({"_id": ObjectId(product_id)}, query)
    return redirect("/LessItems")


@app.route("/editProduct1",methods=['post'])
def editProduct1():
    product_id = ObjectId(request.form.get("product_id"))
    price = request.form.get("price")
    product_quantity = request.form.get("product_quantity")
    threshold_quantity = request.form.get("threshold_quantity")
    query = {"$set": {"price": price, "product_quantity": product_quantity,"threshold_quantity":threshold_quantity}}
    product_col.update_one({"_id": ObjectId(product_id)}, query)
    return redirect("/viewProductDetails?product_id="+str(product_id))



@app.route("/addSalesPerson")
def addSalesPerson():
    return render_template("addSalesPerson.html")


@app.route("/addSalesPerson1",methods=['post'])
def addSalesPerson1():
    name = request.form.get("name")
    email = request.form.get("email")
    phone = request.form.get("phone")
    password = request.form.get("password")
    address = request.form.get("address")
    query = {"$or": [{'email': email,"phone": phone}]}
    count = sales_person_col.count_documents(query)
    if count == 0:
        sales_person_col.insert_one({"name": name,"email": email,"phone": phone,"password": password,"address": address})
        return redirect("/viewSalesPerson")
    else:
        return render_template("message.html",msg='Fail To Add SalesPerson',color='text-danger')


@app.route("/viewSalesPerson")
def viewSalesPerson():
    salesPersons = sales_person_col.find()
    return render_template("viewSalesPerson.html",salesPersons=salesPersons)


@app.route("/stock_manager")
def stock_manager():
    return render_template("stock_manager.html")


@app.route("/addToInvoice",methods=['post'])
def addToInvoice():
    quantity = request.form.get("quantity")
    product_id = ObjectId(request.form.get("product_id"))
    stock_manager_id = session['stock_manager_id']
    query = {"stock_manager_id": ObjectId(stock_manager_id), "status": 'Added To Invoice'}
    a = invoice_col.count_documents(query)
    if a == 0:
        query2 = {"stock_manager_id": ObjectId(stock_manager_id), "status": 'Added To Invoice', "date": datetime.datetime.now()}
        result = invoice_col.insert_one(query2)
        invoice_id = result.inserted_id
    else:
        invoice = invoice_col.find_one({"stock_manager_id": ObjectId(stock_manager_id), "status": 'Added To Invoice'})
        invoice_id = invoice['_id']
    query3 = {'invoice_id': ObjectId(invoice_id), "product_id": ObjectId(product_id)}
    count = invoice_item_col.count_documents(query3)
    if count > 0:
        invoice_item = invoice_item_col.find_one({'invoice_id': ObjectId(invoice_id), "product_id": ObjectId(product_id)})
        Quantity = int(invoice_item['quantity']) + int(quantity)
        query4 = {'$set': {"quantity": Quantity}}
        result10 = invoice_item_col.update_one({'invoice_id': ObjectId(invoice_id), "product_id": ObjectId(product_id)}, query4)

        return render_template("message.html", msg='Quantity Updated', color='text-primary')
    else:
        query6 = {'invoice_id': ObjectId(invoice_id), "product_id": ObjectId(product_id),"quantity": quantity}
        result2 = invoice_item_col.insert_one(query6)
        return render_template("message.html", msg='Product In Invoice', color='text-success')



def getInvoiceId_by_invoiceItems(invoice_id):
    print(invoice_id)
    invoice_items = invoice_item_col.find({"invoice_id":ObjectId(invoice_id)})
    return invoice_items


def getProduct_by_invoice_item(product_id):
    products = product_col.find({"_id":ObjectId(product_id)})
    return products


@app.route("/removeProduct")
def removeProduct():
    invoice_item_id = ObjectId(request.args.get("invoice_item_id"))
    invoice_item = invoice_item_col.find_one({'_id': ObjectId(invoice_item_id)})
    product_id = invoice_item['product_id']
    invoice_id = invoice_item['invoice_id']
    product = product_col.find_one({'_id': ObjectId(product_id)})
    available_quantity = int(product['product_quantity']) + int(invoice_item['quantity'])
    query_quantity = {"$set": {"product_quantity": available_quantity}}
    result = product_col.update_one({'_id': ObjectId(product_id)}, query_quantity)
    result2 = invoice_item_col.delete_one({"_id": ObjectId(invoice_item_id)})
    count = invoice_item_col.count_documents({"invoice_id": ObjectId(invoice_id)})
    if count == 0:
        invoice_col.delete_one({"_id": ObjectId(invoice_id),"stock_manager_id":ObjectId(session['stock_manager_id'])})
    return redirect("/viewSupplierInvoice")



@app.route("/spLogin1",methods=['post'])
def spLogin1():
    email = request.form.get("email")
    password = request.form.get("password")
    query = {"email":email,"password":password}
    count = sales_person_col.count_documents(query)
    if count > 0:
        results = sales_person_col.find(query)
        for result in results:
            session['sales_person_id'] = str(result['_id'])
            session['role'] = "sales_person"
            return render_template("sales_person.html")
    else:
        return render_template("message.html", msg="Invalid login details", color='text-danger')


@app.route("/sales_person")
def sales_person():
    return render_template("sales_person.html")


@app.route("/addCart",methods=['post'])
def addCart():
    quantity = request.form.get("quantity")
    product_id = ObjectId(request.form.get("product_id"))
    sales_person_id = session['sales_person_id']
    query = {"sales_person_id": ObjectId(sales_person_id), "status": 'cart'}
    a = invoice_col.count_documents(query)
    if a == 0:
        query2 = {"sales_person_id": ObjectId(sales_person_id), "status": 'cart', "date": datetime.datetime.now()}
        result = invoice_col.insert_one(query2)
        invoice_id = result.inserted_id
    else:
        invoice = invoice_col.find_one({"sales_person_id": ObjectId(sales_person_id), "status": 'cart'})
        invoice_id = invoice['_id']
    query3 = {'invoice_id': ObjectId(invoice_id), "product_id": ObjectId(product_id)}
    count = invoice_item_col.count_documents(query3)
    if count > 0:
        invoice_item = invoice_item_col.find_one({'invoice_id': ObjectId(invoice_id), "product_id": ObjectId(product_id)})
        Quantity = int(invoice_item['quantity']) + int(quantity)
        query4 = {'$set': {"quantity": Quantity}}
        result10 = invoice_item_col.update_one({'invoice_id': ObjectId(invoice_id), "product_id": ObjectId(product_id)}, query4)
        item = product_col.find_one({'_id': ObjectId(product_id)})
        quantity = int(item['product_quantity']) - int(quantity)
        query7 = {"$set": {"product_quantity": quantity}}
        update2 = product_col.update_one({'_id': ObjectId(product_id)}, query7)
        return render_template("message.html", msg='Quantity Updated', color='text-primary')
    else:
        query6 = {'invoice_id': ObjectId(invoice_id), "product_id": ObjectId(product_id),"quantity": quantity}
        result2 = invoice_item_col.insert_one(query6)
        item = product_col.find_one({'_id': ObjectId(product_id)})
        quantity = int(item['product_quantity']) - int(quantity)
        query8 = {"$set": {"product_quantity": quantity}}
        update3 = product_col.update_one({'_id': ObjectId(product_id)}, query8)
        return render_template("message.html", msg='Add To Cart', color='text-success')

@app.route("/viewCustomerInvoice")
def viewCustomerInvoice():
    status = request.args.get("status")
    query = {}
    if session['role'] == 'sales_person':
        if status == 'cart':
            query = {"sales_person_id":ObjectId(session['sales_person_id']),"status":'cart'}
        elif status == 'Invoice Generated':
            query = {"status":'Ordered',"sales_person_id":ObjectId(session['sales_person_id'])}
    elif session['role'] == 'stock_manager':
        if status == 'Invoice Generated':
            query = {"status": 'Ordered'}
    elif session['role'] == 'owner':
        if status == 'Invoice Generated':
            query = {"status": 'Ordered'}
    invoices = invoice_col.find(query)
    invoices = list(invoices)
    if len(invoices) ==0:
        return render_template("message.html",msg='No Invoices')
    return render_template("viewCustomerInvoice.html",get_customer_by_invoice=get_customer_by_invoice,getSalesPerson_by_Invoice=getSalesPerson_by_Invoice,get_sub_category_id=get_sub_category_id,get_category_sub_category_id=get_category_sub_category_id,invoices=invoices,getInvoiceId_by_invoiceItems=getInvoiceId_by_invoiceItems,getProduct_by_invoice_item=getProduct_by_invoice_item,float=float)


def get_customer_by_invoice(customer_id):
    customer = customer_col.find_one({"_id":ObjectId(customer_id)})
    return customer


def get_category_sub_category_id(sub_category_id):
    sub_category = sub_category_col.find_one({"_id":ObjectId(sub_category_id)})
    category_id = sub_category['category_id']
    category = category_col.find_one({"_id":ObjectId(category_id)})
    return category

def get_sub_category_id(sub_category_id):
    sub_category = sub_category_col.find_one({"_id": ObjectId(sub_category_id)})
    return sub_category


@app.route("/remove")
def remove():
    invoice_item_id = ObjectId(request.args.get("invoice_item_id"))
    invoice_item = invoice_item_col.find_one({'_id': ObjectId(invoice_item_id)})
    product_id = invoice_item['product_id']
    invoice_id = invoice_item['invoice_id']
    product = product_col.find_one({'_id': ObjectId(product_id)})
    available_quantity = int(product['product_quantity']) + int(invoice_item['quantity'])
    query_quantity = {"$set": {"product_quantity": available_quantity}}
    result = product_col.update_one({'_id': ObjectId(product_id)}, query_quantity)
    result2 = invoice_item_col.delete_one({"_id": ObjectId(invoice_item_id)})
    count = invoice_item_col.count_documents({"invoice_id": ObjectId(invoice_id)})
    if count == 0:
        invoice_col.delete_one({"_id": ObjectId(invoice_id),"sales_person_id":ObjectId(session['sales_person_id'])})
    return redirect("/viewCustomerInvoice")


@app.route("/generateBill",methods=['post'])
def generateBill():
    invoice_id = ObjectId(request.form.get("invoice_id"))
    name = request.form.get("name")
    email = request.form.get("email")
    phone = request.form.get("phone")
    count = customer_col.count_documents({"$or":[{"email":email},{"phone":phone}]})
    if count >0:
        return render_template("message.html",msg='Duplicate Customer Details',color='text-danger')
    else:
        result = customer_col.insert_one({"name": name,"email": email,"phone": phone})
        customer_id = result.inserted_id
        query = {"$set":{"status": 'Ordered',"customer_id":ObjectId(customer_id)}}
        invoice_col.update_one({'_id': ObjectId(invoice_id)},query)
        return redirect("/viewCustomerInvoice?status=Invoice Generated")


def getSalesPerson_by_Invoice(sales_person_id):
    sales_person = sales_person_col.find_one({'_id':ObjectId(sales_person_id)})
    return sales_person




@app.route("/LessItems")
def LessItems():
    query = {}
    products = product_col.find()
    products2 = []
    for product in products:
        if int(product['product_quantity']) <= int(product['threshold_quantity']):
            products2.append(product)
    products2 = list(products2)
    if len(products2) == 0:
        return render_template("message.html",msg='No Less Items')
    return render_template("LessItems.html",products=products2,get_sub_category_by_products=get_sub_category_by_products,get_category_by_products=get_category_by_products)


@app.route("/view_customers")
def view_customers():
    customers = customer_col.find()
    return render_template("view_customers.html", customers=customers)


app.run(debug=True)
