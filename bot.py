import discord
import urllib.parse
import os
from dotenv import load_dotenv

# === TẢI BIẾN MÔI TRƯỜNG ===
load_dotenv()

# Bắt buộc — ĐÃ SỬA THEO YÊU CẦU
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    print("❌ Thiếu TOKEN trong file .env!")
    exit()

# Tùy chọn — dùng mặc định nếu không có trong .env
ADMIN_ID = int(os.getenv("ADMIN_ID", 1479375774711549996))
KENH_ADMIN_ID = int(os.getenv("KENH_ADMIN_ID", 1548859373550444616))
KENH_TICKET_ID = int(os.getenv("KENH_TICKET_ID", 1547096938141323346))

STK_BANK = os.getenv("STK_BANK", "070144429018")
TEN_CHU_TK = os.getenv("TEN_CHU_TK", "NGUYEN THI PHUONG")
NGAN_HANG = os.getenv("NGAN_HANG", "sacombank")
TEMPLATE_QR = "compact2"

FILE_SO_DON = "so_don_tiep.txt"

# === QUẢN LÝ SỐ ĐƠN — LƯU VĨNH VIỄN ===
def doc_so_don():
    if os.path.exists(FILE_SO_DON):
        with open(FILE_SO_DON, "r") as f:
            return int(f.read().strip())
    return 1

def luu_so_don(gia_tri):
    with open(FILE_SO_DON, "w") as f:
        f.write(str(gia_tri))

so_don_tiep = doc_so_don()
don_dang_xu_ly = {}
don_hang = {}

# === TẠO LINK QR VIETQR ===
def tao_link_qr(stk, bank_code, so_tien, ghi_chu, ten_chu_tk):
    ghi_chu_ma = urllib.parse.quote(ghi_chu)
    ten_ma = urllib.parse.quote(ten_chu_tk)
    return f"https://img.vietqr.io/image/{bank_code}-{stk}-{TEMPLATE_QR}.jpg?amount={so_tien}&addInfo={ghi_chu_ma}&accountName={ten_ma}"

# === NÚT XỬ LÝ ĐƠN HÀNG ===
class XuLyDonHang(discord.ui.View):
    def __init__(self, ma_don, id_khach):
        super().__init__(timeout=None)
        self.ma_don = ma_don
        self.id_khach = id_khach

    async def kiem_tra_quyen(self, interaction):
        if interaction.user.id != ADMIN_ID:
            await interaction.response.send_message("❌ Chỉ Admin được xử lý đơn hàng!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="❌ Hủy Đơn", style=discord.ButtonStyle.danger, row=0)
    async def nut_huy(self, interaction, button):
        if not await self.kiem_tra_quyen(interaction): return
        don_dang_xu_ly.pop(self.id_khach, None)
        em = interaction.message.embeds[0]
        em.title = f"❌ ĐƠN {self.ma_don} - ĐÃ HỦY"
        em.color = discord.Color.dark_red()
        await interaction.message.edit(
            content=f"🛑 Đơn bị hủy bởi **{interaction.user.mention}**",
            embed=em, view=None
        )
        await interaction.response.defer()

    @discord.ui.button(label="🔎 Đã Kiểm Tra", style=discord.ButtonStyle.secondary, row=0)
    async def nut_kiemtra(self, interaction, button):
        if not await self.kiem_tra_quyen(interaction): return
        em = interaction.message.embeds[0]
        em.description += "\n✅ **Đã đối chiếu thông tin**"
        await interaction.message.edit(embed=em, view=self)
        await interaction.response.defer()

    @discord.ui.button(label="✅ Hoàn Tất", style=discord.ButtonStyle.success, row=0)
    async def nut_hoanthanh(self, interaction, button):
        if not await self.kiem_tra_quyen(interaction): return
        don_dang_xu_ly.pop(self.id_khach, None)
        em = interaction.message.embeds[0]
        em.title = f"✅ {self.ma_don} - HOÀN TẤT"
        em.color = discord.Color.green()
        em.description += "\n🎉 **Đơn hàng đã hoàn tất!**"
        await interaction.message.edit(
            content=f"🟢 **{interaction.user.mention}** đã duyệt & hoàn tất",
            embed=em, view=None
        )
        await interaction.response.defer()

# === BOT CHÍNH ===
class BloxStoreBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)

    async def on_ready(self):
        global so_don_tiep
        so_don_tiep = doc_so_don()
        print(f"\n===== 🛒 BLOX STORE BOT =====")
        print(f"🤖 Đăng nhập: {self.user}")
        print(f"🏷️ Đơn tiếp theo: BL{so_don_tiep:03d}")
        print(f"✅ Sẵn sàng!\n")

    async def on_message(self, message):
        global so_don_tiep
        if message.author.bot or not message.guild:
            return

        if message.content.lower().startswith("!ord "):
            nguoi_mua = message.author

            if nguoi_mua.id in don_dang_xu_ly:
                return await message.reply(
                    f"⚠️ Bạn còn đơn **{don_dang_xu_ly[nguoi_mua.id]}** chưa xong!\n"
                    "Chờ hoặc liên hệ Admin.", ephemeral=True
                )

            try:
                phan_tu = message.content.split()
                gia_tri = int(phan_tu[-1])
                ten_sp = " ".join(phan_tu[1:-1]).strip()
                if not ten_sp: raise ValueError()
                gia_dang = f"{gia_tri:,}đ"
            except:
                return await message.reply(
                    "❌ Sai cú pháp!\n`!ord [Tên SP] [Số tiền]`\nVD: `!ord Vip 50000`",
                    ephemeral=True
                )

            ma_hoa_don = f"BL{so_don_tiep:03d}"
            noi_dung_ck = f"{ten_sp.upper()} {ma_hoa_don}"
            link_qr = tao_link_qr(STK_BANK, NGAN_HANG, gia_tri, noi_dung_ck, TEN_CHU_TK)
            link_ho_tro = f"https://discord.com/channels/{message.guild.id}/{KENH_TICKET_ID}"

            don_dang_xu_ly[nguoi_mua.id] = ma_hoa_don
            so_don_tiep += 1
            luu_so_don(so_don_tiep)

            # === Gửi cho khách ===
            embed_hoa_don = discord.Embed(
                title=f"🧾 HÓA ĐƠN: {ma_hoa_don}",
                description=(
                    f"👤 Khách: {nguoi_mua.mention}\n"
                    f"📦 Sản phẩm: **{ten_sp}**\n"
                    f"💸 Thành tiền: **{gia_dang}**\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"🏦 {NGAN_HANG.upper()} | TK: `{STK_BANK}`\n"
                    f"Chủ TK: `{TEN_CHU_TK}`\n"
                    f"📝 Nội dung CK: `{noi_dung_ck}`\n\n"
                    f"⏳ Trạng thái: **Chờ xác nhận**"
                ),
                color=0x3498db
            )
            embed_hoa_don.set_image(url=link_qr)
            embed_hoa_don.set_footer(text="Blox Store — An toàn & Minh bạch")

            gui_tin = await message.channel.send(
                f"━━━━━━ 🛒 **ĐƠN HÀNG MỚI** ━━━━━━",
                embed=embed_hoa_don,
                view=discord.ui.View().add_item(
                    discord.ui.Button(label="🎫 Hỗ trợ/Ticket", url=link_ho_tro)
                )
            )

            # === Gửi cho Admin xử lý ===
            embed_admin = discord.Embed(
                title=f"📥 ĐƠN MỚI CHỜ DUYỆT: {ma_hoa_don}",
                description=(
                    f"Khách: {nguoi_mua.mention} (`{nguoi_mua.id}`)\n"
                    f"Sản phẩm: **{ten_sp}**\nGiá: `{gia_dang}`\n"
                    f"Ghi chú: `{noi_dung_ck}`"
                ),
                color=0xf39c12
            )
            kenh_admin = self.get_channel(KENH_ADMIN_ID) or await self.fetch_channel(KENH_ADMIN_ID)
            await kenh_admin.send(
                f"🔔 <@{ADMIN_ID}> CÓ ĐƠN MỚI!",
                embed=embed_admin,
                view=XuLyDonHang(ma_hoa_don, nguoi_mua.id)
            )

            await message.reply(f"✅ **{ma_hoa_don} đã tạo!** Chuyển khoản với nội dung `{noi_dung_ck}` rồi chờ Admin nhé.")

bot = BloxStoreBot()
bot.run(TOKEN)
      
