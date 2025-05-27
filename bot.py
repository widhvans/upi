import qrcode
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config import TOKEN, UPI_ID, MERCHANT_NAME, PAYMENT_AMOUNT
import asyncio

# Mock payment verification (replace with actual payment gateway API)
async def verify_payment(utr: str) -> bool:
    # Simulate payment verification logic
    return len(utr) == 12  # Example: UTR is typically 12 digits

# Generate UPI QR code
def generate_upi_qr(upi_id: str, merchant_name: str, amount: float) -> str:
    upi_url = f"upi://pay?pa={upi_id}&pn={merchant_name}&am={amount}&cu=INR"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(upi_url)
    qr.make(fit=True)
    qr_image = qr.make_image(fill='black', back_color='white')
    qr_path = "upi_qr.png"
    qr_image.save(qr_path)
    return qr_path

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    qr_path = generate_upi_qr(UPI_ID, MERCHANT_NAME, PAYMENT_AMOUNT)
    await update.message.reply_photo(photo=open(qr_path, 'rb'), 
                                   caption=f"Scan this QR to pay ₹{PAYMENT_AMOUNT} to {MERCHANT_NAME}. After payment, send the UTR number.")
    os.remove(qr_path)

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
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_utr))
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
