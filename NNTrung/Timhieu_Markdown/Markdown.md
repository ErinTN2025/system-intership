# 📚 **MARKDOWN LEARNING** 
## Phụ lục
- [📚 **MARKDOWN LEARNING**](#-markdown-learning)
  - [Phụ lục](#phụ-lục)
  - [1 **Tiêu đề (Heading)**](#1-tiêu-đề-heading)
  - [2 **In đậm, In nghiêng, Gạch ngang**](#2-in-đậm-in-nghiêng-gạch-ngang)
  - [3 **Link**](#3-link)
  - [4 **Code**](#4-code)
  - [5 **Danh sách**](#5-danh-sách)
  - [6 **Quote**](#6-quote)
  - [7 **Bảng**](#7-bảng)
  - [8 **Checklist**](#8-checklist)
  - [9 **Chú thích (Footnote)**](#9-chú-thích-footnote)
  - [10 **Hình ảnh  (Image)**](#10-hình-ảnh--image)
<!-- TOC -->
<!-- /TOC -->

---

## 1 **Tiêu đề (Heading)**

```markdown
# Heading 1

## Heading 2

### Heading 3

#### Heading 4
```

---

## 2 **In đậm, In nghiêng, Gạch ngang**

* **In đậm:** `**Bold**` → **Bold**

* *In nghiêng:* `_Italic_` → *Italic*

* ***Vừa đậm vừa nghiêng:*** `**_Italic_**` → ***Italic***

* ~~Gạch ngang (Strikethrough):~~ `~~Strikethrough~~` → ~~Strikethrough~~

---

## 3 **Link**

```markdown
[Input link](https://topdev.vn/blog/markdown-la-gi-cach-su-dung-markdown)
```

[Input link](https://topdev.vn/blog/markdown-la-gi-cach-su-dung-markdown)

---

## 4 **Code**

**Code inline:** `` `Print "Hello World"` ``  `Print "Hello World"`

**Code block Python:**

```python
print(f"Hello, {name}!")
```

**Code block CSS:**

```css
.ast-separate-container .ast-comment-list li.depth-1 {
  padding: 0.625rem;
  border-bottom: 1px solid #eee;
}

.single .nav-links .nav-previous,
.single .nav-links .nav-next,
.single .ast-author-details .author-title,
.ast-comment-meta {
  font-size: 20px;
}

time {
  font-size: 16px;
}

@media (min-width: 768px) {
  .ast-separate-container.ast-two-container.ast-right-sidebar #secondary {
    padding-left: 0;
  }
}

.ast-comment-time {
  margin-top: -10px;
}

.ast-comment-list {
  font-size: 18px;
}

.ast-separate-container .comment-reply-title {
  font-size: 24px;
  font-weight: bold;
}
```

---

## 5 **Danh sách**

* line 1

  * line 1.1

  - line 1.2

- line 2

  * line 2.1
  * line 2.2

* line 3

  * line 3.1
  * line 3.2

---

## 6 **Quote**

```markdown
> Đây là Quote cấp 1
>> Đây là Quote cấp 2
```

> Đây là Quote cấp 1
>
> > Đây là Quote cấp 2

---

## 7 **Bảng**

| Họ tên    | Tuổi |         Địa chỉ |
| :-------- | :--: | --------------: |
| Nguyễn An |  25  |          Hà Nội |
| Trần Bình |  30  | TP. Hồ Chí Minh |
| Lê Cường  |  22  |         Đà Nẵng |

---

## 8 **Checklist**

* [x] Việc đã xong
* [ ] Việc chưa xong

---

## 9 **Chú thích (Footnote)**

Đây là một chú thích[^1].

[^1]: Nội dung chú thích ở cuối tài liệu.

---
## 10 **Hình ảnh  (Image)**

![Landscape](https://www.adorama.com/alc/wp-content/uploads/2018/11/landscape-photography-tips-yosemite-valley-feature.jpg)