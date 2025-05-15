from robocorp.tasks import task
from robocorp import browser

from RPA.HTTP import HTTP
from RPA.Tables import Tables
from RPA.PDF import PDF
from RPA.Archive import Archive

ROBOT_ORDERS_URL = "https://robotsparebinindustries.com/#/robot-order"
ORDERS_CSV = "https://robotsparebinindustries.com/orders.csv"

@task
def order_robots_from_RobotSpareBin():
    """
    Orders robots from RobotSpareBin Industries Inc.
    Saves the order HTML receipt as a PDF file.
    Saves the screenshot of the ordered robot.
    Embeds the screenshot of the robot to the PDF receipt.
    Creates ZIP archive of the receipts and the images.
    """
    open_robot_order_website()
    
    orders = get_orders()
    for order in orders:
        close_annoying_modal()
        fill_the_form(order)
    archive_receipts()

def open_robot_order_website():
    browser.configure()
    page = browser.page()
    page.goto(ROBOT_ORDERS_URL)

def get_orders():
    """Downloads csv file from the given URL"""
    http = HTTP()
    library = Tables()
    http.download(url=ORDERS_CSV, overwrite=True)
    orders = library.read_table_from_csv(
        "orders.csv", columns=["Order number", "Head", "Body", "Legs", "Address"]
    )
    return orders

def close_annoying_modal():
    page = browser.page()
    page.click("button:text('OK')")
    
def fill_the_form(order):
    page = browser.page()
    page.select_option("select#head", value=order["Head"])
    page.click(f"input#id-body-{order['Body']}")
    page.fill("input[placeholder='Enter the part number for the legs']", order['Legs'])
    page.fill("input#address", order["Address"])
    page.click("button#preview")
    submit_the_order()
    receipt_pdf = store_receipt_as_pdf(order["Order number"])
    robot_screenshot = screenshot_robot(order["Order number"])
    embed_screenshot_to_receipt(robot_screenshot, receipt_pdf)
    page.click("button#order-another")

def submit_the_order():
    """Submit selected order"""
    page = browser.page()
    page.click("button#order")
    tries = 0
    while page.query_selector("div.alert.alert-danger[role='alert']") and tries < 10:
        page.click("button#order")
        tries += 1

def store_receipt_as_pdf(order_number):
    """Export the data to a pdf file"""
    page = browser.page()
    receipt_html = page.locator("#order-completion").inner_html()
    pdf = PDF()
    receipt_path = f"output/receipt_{order_number}.pdf"
    pdf.html_to_pdf(receipt_html, receipt_path)
    return receipt_path

def screenshot_robot(order_number):
    """Capture configured robot"""
    page = browser.page()
    robot_html = page.locator("#robot-preview-image")
    screenshot_path = f"output/robot_{order_number}.png"
    robot_html.screenshot(path=screenshot_path)
    return screenshot_path

def embed_screenshot_to_receipt(screenshot, pdf_file):
    """Append robot image to the receipt"""
    pdf = PDF()
    list_of_files = [screenshot]
    pdf.add_files_to_pdf(files=list_of_files, target_document=pdf_file, append=True)

def archive_receipts():
    """Create handful archive with all receipts"""
    receipts_archive = Archive()
    receipts_archive.archive_folder_with_zip('./output', 'output/receipts.zip', include='*.pdf')
