# Khi tạo User trên cloud thường bị nhiễm lỗi ký tự

Trong đa số trường hợp **`/etc/skel/.profile` và `/etc/skel/.bashrc` cũng bị nhiễm XML** → nên lệnh `cp /etc/skel/...`  chỉ copy file hỏng đè lên file hỏng.

Hệ thống `/etc/profile` và `/etc/bash.bashrc` vẫn ổn nên fix xong là dùng bình thường.

## Fix (chạy từng block)

### 1. Tạo `.profile` cho kolla

```bash
sudo tee /home/kolla/.profile > /dev/null << 'EOF'
# ~/.profile: executed by the command interpreter for login shells.

if [ -n "$BASH_VERSION" ]; then
    if [ -f "$HOME/.bashrc" ]; then
        . "$HOME/.bashrc"
    fi
fi

if [ -d "$HOME/bin" ] ; then
    PATH="$HOME/bin:$PATH"
fi

if [ -d "$HOME/.local/bin" ] ; then
    PATH="$HOME/.local/bin:$PATH"
fi
EOF
```

### 2. Tạo `.bashrc` cho kolla

```bash
sudo tee /home/kolla/.bashrc > /dev/null << 'EOF'
# ~/.bashrc: executed by bash(1) for non-login shells.
case $- in
    *i*) ;;
      *) return;;
esac

HISTCONTROL=ignoreboth
shopt -s histappend
HISTSIZE=1000
HISTFILESIZE=2000
shopt -s checkwinsize

PS1='\u@\h:\w\$ '

if [ -x /usr/bin/dircolors ]; then
    test -r ~/.dircolors && eval "$(dircolors -b ~/.dircolors)" || eval "$(dircolors -b)"
    alias ls='ls --color=auto'
    alias grep='grep --color=auto'
fi

alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'
EOF
```

### 3. Set quyền

```bash
sudo chown kolla:kolla /home/kolla/.profile /home/kolla/.bashrc
sudo chmod 644 /home/kolla/.profile /home/kolla/.bashrc
```

### 4. Verify trước khi test

```bash
sudo head -3 /home/kolla/.profile
sudo head -3 /home/kolla/.bashrc
```

Phải thấy dòng comment `# ~/.profile:...` và `# ~/.bashrc:...`, **không phải** XML nữa.

### 5. Test

```bash
su - kolla
```

---

## Fix luôn `/etc/skel` (quan trọng cho tương lai)

Để các user mới tạo sau này không bị dính lỗi tương tự:

```bash
sudo cp /home/kolla/.profile /etc/skel/.profile
sudo cp /home/kolla/.bashrc /etc/skel/.bashrc
sudo chown root:root /etc/skel/.profile /etc/skel/.bashrc
sudo chmod 644 /etc/skel/.profile /etc/skel/.bashrc
```

---

## Kiểm tra thêm các user khác

Vì `/etc/skel` đã bị nhiễm, có thể các user khác cũng dính:

```bash
sudo head -1 /root/.profile 2>/dev/null
sudo head -1 /root/.bashrc 2>/dev/null

# Liệt kê tất cả home dir
for u in $(ls /home); do
  echo "=== $u ==="
  sudo head -1 /home/$u/.profile 2>/dev/null
  sudo head -1 /home/$u/.bashrc 2>/dev/null
done
```

User nào có dòng `<?xml...` thì fix tương tự bằng cách copy file lành từ `/home/kolla/` sang.

---

## Tìm thủ phạm

Khi đã vào được shell kolla, kiểm tra xem ai gây ra:

```bash
sudo grep -rE 'wget.*profile|curl.*profile|wget.*bashrc|curl.*bashrc|vnptcloud' /root/.bash_history /home/*/.bash_history 2>/dev/null
```

Khả năng cao là một script cài đặt nào đó (có thể là script chuẩn bị môi trường kolla-ansible) tải file từ bucket VNPT Cloud nhưng bucket trả về `AccessDenied`, rồi script vẫn ghi response vào file cấu hình.