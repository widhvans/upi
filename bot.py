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
    await update.message.reply_text("Please send the amount for the UPI QR code (e.g., '10' for ₹10).")

# Handle amount input
async def handle_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == "10":
        qr_path = generate_upi_qr(UPI_ID, 10.00)
        await update.message.reply_photo(photo=open(qr_path, 'rb'), 
                                       caption="Scan this QR to pay ₹10. After payment, send the UTR number.")
        os.remove(qr_path)
    else:
        await update.message.reply_text("Please send '10' for a ₹10 QR code.")

# Handle UTR input
async def handle_utr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    utr = update.message.text.strip()
    if await verify_payment(utr):
        await update.message.reply_text("Payment verified successfully!")
    else:
        await update.message.reply_text("Payment verification failed. Please check the UTR and try again.")

async def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_amount))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_utr))
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
