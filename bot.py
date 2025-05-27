import qrcode
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config import TOKEN, UPI_ID, RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET
import asyncio
import razorpay
import re

# Initialize Razorpay client
razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

# Verify payment using Razorpay API
async def verify_payment(utr: str, order_id: str) -> bool:
    try:
        # Fetch payment details by UTR
        payments = razorpay_client.payment.fetch_all({"utr": utr})
        for payment in payments.get("items", []):
            if payment["order_id"] == order_id and payment["status"] == "captured":
                return True
        return False
    except Exception:
        return False

# Generate UPI QR code
def generate_upi_qr(upi_id: str, amount: float) -> str:
    upi_url = f"upi://pay?pa={upi_id}&am={amount}&cu=INR"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(upi_url)
    qr.make(fit=True)
    qr_image = qr.make_image(fill='black', back_color='white')
    qr_path = f"upi_qr_{int(amount)}.png"
    qr_image.save(qr_path)
    return qr_path

# Create Razorpay order
def create_razorpay_order(amount: float) -> str:
    order = razorpay_client.order.create({
        "amount": int(amount * 100),  # Amount in paise
        "currency": "INR",
        "payment_capture": 1  # Auto-capture payment
    })
    return order["id"]

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['state'] = 'awaiting_amount'
    await update.message.reply_text("Please send the amount for the UPI QR code (e.g., '50' for ₹50).")

# Handle text input based on state
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    state = context.user_data.get('state', 'awaiting_amount')

    if state == 'awaiting_amount':
        if re.match(r'^\d+(\.\d{1,2})?$', text):  # Validate numeric amount
            amount = float(text)
            if amount > 0:
                # Create Razorpay order
                order_id = create_razorpay_order(amount)
                context.user_data['order_id'] = order_id
                
                # Generate QR code
                qr_path = generate_upi_qr(UPI_ID, amount)
                await update.message.reply_photo(
                    photo=open(qr_path, 'rb'),
                    caption=f"Scan this QR to pay ₹{amount}. After payment, send the UTR number."
                )
                os.remove(qr_path)
                context.user_data['state'] = 'awaiting_utr'
            else:
                await update.message.reply_text("Please send a valid amount greater than 0.")
        else:
            await update.message.reply_text("Please send a valid numeric amount (e.g., '50' or '50.00').")
    elif state == 'awaiting_utr':
        order_id = context.user_data.get('order_id')
        if order_id and await verify_payment(text, order_id):
            await update.message.reply_text("Payment verified successfully!")
            context.user_data['state'] = 'awaiting_amount'  # Reset state
            context.user_data.pop('order_id', None)
        else:
            await update.message.reply_text("Payment verification failed. Please check the UTR and try again.")

async def main():
    # Create application
    app = Application.builder().token(TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    # Initialize and start polling
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    
    # Run until interrupted
    try:
        while True:
            await asyncio.sleep(3600)  # Sleep to keep the loop alive
    except KeyboardInterrupt:
        pass
    finally:
        # Properly shut down
        await app.updater.stop()
        await app.stop()
        await app.shutdown()

if __name__ == "__main__":
    # Create a new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
