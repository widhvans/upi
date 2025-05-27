import qrcode
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config import TOKEN, UPI_ID
import asyncio

# Mock payment verification (replace with actual payment gateway API)
async def verify_payment(utr: str) -> bool:
    return len(utr) == 12  # Example: UTR is typically 12 digits

# Generate UPI QR code
def generate_upi_qr(upi_id: str, amount: float = 10.00) -> str:
    upi_url = f"upi://pay?pa={upi_id}&am={amount}&cu=INR"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(upi_url)
    qr.make(fit=True)
    qr_image = qr.make_image(fill='black', back_color='white')
    qr_path = "upi_qr.png"
    qr_image.save(qr_path)
    return qr_path

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['state'] = 'awaiting_amount'
    await update.message.reply_text("Please send the amount for the UPI QR code (e.g., '10' for ₹10).")

# Handle text input based on state
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    state = context.user_data.get('state', 'awaiting_amount')

    if state == 'awaiting_amount':
        if text == "10":
            qr_path = generate_upi_qr(UPI_ID, 10.00)
            await update.message.reply_photo(photo=open(qr_path, 'rb'), 
                                           caption="Scan this QR to pay ₹10. After payment, send the UTR number.")
            os.remove(qr_path)
            context.user_data['state'] = 'awaiting_utr'
        else:
            await update.message.reply_text("Please send '10' for a ₹10 QR code.")
    elif state == 'awaiting_utr':
        if await verify_payment(text):
            await update.message.reply_text("Payment verified successfully!")
            context.user_data['state'] = 'awaiting_amount'  # Reset state
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
