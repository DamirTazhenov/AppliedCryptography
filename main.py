from des import *

from pywebio import start_server
from pywebio.input import *
from pywebio.output import *
from pywebio.session import run_async, run_js

chat_msgs = []
online_users = set()

MAX_MESSAGES_COUNT = 150

async def main():
    global chat_msgs

    nickname = await input(required=True, placeholder="Your name:",
                           validate=lambda n: "Username's already in use." if n in online_users or n == '[INFO]' else None)

    msg_box = output()
    put_scrollable(msg_box, height=300, keep_bottom=True)
    
    online_users.add(nickname)

    chat_msgs.append(('[INFO]', f'`{nickname}` joined.'))
    msg_box.append(put_markdown(f'`{nickname}` join the chat'))

    refresh_task = run_async(refresh_msg(nickname, msg_box))

    while True:
        data = await input_group("| Internet Relay Chat |", [
            input(placeholder="...", name="msg"),
            file_upload(accept='.txt,.pdf,.doc', name='file', help_text='Choose a file (txt, pdf, doc)'),
            actions(name="cmd", buttons=["Send", {'label': "Log out", 'type': 'cancel'}])
        ], validate=lambda m: ('msg', "Enter the message") if m["cmd"] == "Send" and not m['msg'] and not m['file'] else None)

        if data is None:
            break
        put_table = [
            [],
            []
        ]
        # Process file if uploaded
        file_content = ""
        if 'file' in data and data['file']:
            file_content = data['file']['content'].decode('latin-1')
            encrypted_file = bin2hex(encrypt(file_content.encode().hex(), rkb, rk))
            msg_box.append(put_markdown(f"`{nickname}` (Encrypted File): {encrypted_file}, {file_content}"))
            chat_msgs.append((nickname, encrypted_file))

        # Process text message if provided
        if 'msg' in data:
            encrypted_msg = bin2hex(encrypt(data['msg'].encode('UTF-8').hex(), rkb, rk))
            msg_box.append(put_markdown(f"`{nickname}` (Encrypted): {encrypted_msg} ({data['msg']})"))
            chat_msgs.append((nickname, encrypted_msg))

    refresh_task.close()

    online_users.remove(nickname)
    toast("You have logged out of the chat.")
    msg_box.append(put_markdown(f'[INFO] User `{nickname}` left the chat.'))
    chat_msgs.append(('[INFO]', f'User `{nickname}` left the chat.'))

    put_buttons(['Re-visit'], onclick=lambda btn: run_js('window.location.reload()'))

async def refresh_msg(nickname, msg_box):
    global chat_msgs
    last_idx = len(chat_msgs)

    while True:
        await asyncio.sleep(1)

        for m in chat_msgs[last_idx:]:
            if m[0] != nickname:  # if not a message from the current user
                if all(c in "0123456789ABCDEFabcdef" for c in m[1]):
                    decrypted_msg = bytes.fromhex(bin2hex(encrypt(m[1], rkb[::-1], rk[::-1]))).decode('UTF-8')
                    msg_box.append(put_markdown(f"`{m[0]}` (Decrypted): {decrypted_msg}"))
                else:
                    msg_box.append(put_markdown(f"`{m[0]}`: {m[1]}"))

        # remove expired
        if len(chat_msgs) > MAX_MESSAGES_COUNT:
            chat_msgs = chat_msgs[len(chat_msgs) // 2:]

        last_idx = len(chat_msgs)



if __name__ == "__main__":
    key = "AABB09182736CCDD"
    key = hex2bin(key)
    key = permute(key, keyp, 56)

    left = key[0:28]
    right = key[28:56]

    rkb = []
    rk = []
    for i in range(0, 16):
        left = shift_left(left, shift_table[i])
        right = shift_left(right, shift_table[i])

        combine_str = left + right
        round_key = permute(combine_str, key_comp, 48)

        rkb.append(round_key)
        rk.append(bin2hex(round_key))

    start_server(main, debug=True, port=8080, cdn=False)