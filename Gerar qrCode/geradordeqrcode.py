import qrcode

# Defina o link para o qual você deseja gerar o QR Code
link = "https://casamentoanaepedro2024.com.br/"

# Crie um objeto QRCode
qr = qrcode.QRCode(
    version=1,  # controla o tamanho do QR Code
    error_correction=qrcode.constants.ERROR_CORRECT_L,  # nível de correção de erro
    box_size=10,  # tamanho de cada "caixa" do código QR
    border=4,  # espessura da borda
)

# Adicione o link ao QR Code
qr.add_data(link)
qr.make(fit=True)

# Crie uma imagem do QR Code
img = qr.make_image(fill='black', back_color='white')

# Salve a imagem em um arquivo
img.save("qrcode_casamentoanaepedro.png")

print("QR Code gerado e salvo como 'qrcode_site.png'")
