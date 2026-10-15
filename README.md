# TechStore

A small online shop for smartphones and tablets, built with Django 5.2.

I wanted something you can unzip, run, and actually hand to a shop owner: a clean storefront on one side, and a proper management panel on the other, where the owner can change almost anything without touching code. That's what this is. It is not a demo mockup, but it is also not finished in every direction, so there's an honest "what's missing" section near the bottom.

## Before you start: please read this

I wrote this project in an environment where Django could not be installed, so I could never run it. The code compiles, the templates were checked for broken tags and wrong URL names, and I wrote a test suite, but **none of it has been executed against a real Django install yet**. Your first run is the real test.

So, once you've installed everything, run these three before anything else:

```bash
python manage.py check
python manage.py migrate
python manage.py test
```

If something breaks, send me the error and I'll fix it. After `migrate`, `python manage.py makemigrations --check --dry-run` should say there are no changes. If it doesn't, that's worth telling me too.

## What you need

Python 3.13 (anything from 3.10 up works with Django 5.2) and pip. That's it. The database is SQLite, and the only packages are Django 5.2.7 and Pillow.

## Getting it running

```bash
python -m venv venv
source venv/bin/activate          # on Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env              # on Windows: copy .env.example .env
```

Open `.env` and set `DJANGO_DEBUG=True` for local work. Also put something in `DJANGO_SECRET_KEY`. This will generate one:

```bash
python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"
```

Then:

```bash
python manage.py check
python manage.py migrate
python manage.py seed_demo_data
python manage.py createsuperuser
python manage.py runserver
```

The shop is at http://127.0.0.1:8000/ and the panel is at http://127.0.0.1:8000/manage/.

There is no default admin account or password anywhere in this project. You create your own with `createsuperuser`. You can pick any username, but you log in with the email address you gave it.

## The sample data

`seed_demo_data` fills the shop with two brands, two categories, eight products (four phones, four tablets), a finished-looking home page, a menu, a footer and a few text pages. The images are simple device illustrations I generated for this project, so you can use them however you like.

Please treat the prices and specs as placeholders. They are made up for the demo and are not real market data. One product version is deliberately out of stock so you can see how that looks.

You can run the command as many times as you want. It only creates what's missing and never touches things you've already edited.

## Using the management panel

Everything lives under `/manage/`. The normal Django Admin isn't installed at all, this panel replaces it. Only accounts with staff status can get in, and the check happens on the server, so guessing URLs won't help a regular customer.

A few things you'll probably want to know:

**Products** have "versions". A version is one storage size plus one color, with its own price, sale price and stock, so an iPhone in 128GB Black and 256GB Blue are two versions of the same product. Storage sizes and colors are managed on their own pages, so you're never stuck with a fixed list. Specs like RAM or battery are optional, and if you leave one empty it simply doesn't appear on the product page.

**The home page** is a stack of sections (hero banner, new arrivals, best sellers, categories, promos, and so on). You can edit each one's text, images, colors and spacing, turn it off, delete it, or move it up and down with the arrows.

**Appearance** is where you pick a design profile (Modern Blue, Midnight Black, Minimal White, Premium Dark, Tech Purple) and then tweak colors, fonts, text sizes and layout. There's a live preview on the page, a button to discard what you haven't saved, and one to reset everything. Nothing changes on the real shop until you hit Save.

**Footer, menu, store settings and text pages** are all editable too: name, logo, contact details, link columns, social links, copyright line, an announcement bar, and so on.

When you delete something, you're asked to confirm. If a brand or category still has products, the panel refuses and suggests deactivating it instead, which is usually what you actually want. Image files are only removed from disk when nothing else uses them.

## How the shop behaves

Customers can browse, search and filter by category, brand, storage, color, price and availability. They can add things to a cart without an account, but they need to sign in (or register, which asks for an address) before they can go on to checkout. A guest's cart is merged into their account when they log in. Prices and stock are always read from the database on the server, never trusted from the browser.

"Best sellers" works like this: if real sales numbers exist, it uses them. If not, it shows the products you've marked as your picks.

## What's missing on purpose

There's no payment gateway, no wallet, and no fake payment. The checkout page shows the order summary and delivery address, then tells the customer that payment isn't available yet. There are also no order records, so nothing can actually be placed. You didn't ask for orders in this round, so I didn't add them, but the cart is built so an order step can be added later without redoing things.

Also not included: login rate limiting, email verification, password-reset emails, and any production setup (HTTPS, a real database, backups). Add those before putting this on the public internet.

## Images, fonts and static files

Uploads go into `media/`, sorted into folders (`products/`, `brands/`, `sections/`, and so on). Allowed image types are JPG, PNG and WEBP up to 5 MB. SVG is refused on purpose. The app checks the real file content and not just the extension. Custom fonts (TTF, OTF, WOFF, WOFF2, up to 2 MB) can be uploaded from the panel. Please only upload fonts you're licensed to use. I didn't bundle any, the defaults are plain system fonts.

While `DEBUG=True`, Django serves everything for you. In production you'll need to run `python manage.py collectstatic` and serve `staticfiles/` and `media/` from your web server.

## Settings you can put in `.env`

- `DJANGO_DEBUG`: `True` for development, `False` in production.
- `DJANGO_SECRET_KEY`: required whenever debug is off.
- `DJANGO_ALLOWED_HOSTS`: comma-separated hostnames (default is `localhost,127.0.0.1`).
- `DJANGO_CSRF_TRUSTED_ORIGINS`: comma-separated origins like `https://shop.example.com`, when you deploy.
- `DJANGO_SECURE_COOKIES`: secure cookies when debug is off (on by default).

Never commit your real `.env`.

## When something goes wrong

- *"DJANGO_SECRET_KEY is not set"*: you skipped the `.env` step, or debug is off. Create `.env` and fill it in.
- *`DisallowedHost`*: add your domain to `DJANGO_ALLOWED_HOSTS`.
- *No styling in production*: run `collectstatic` and serve the `staticfiles/` folder.
- *Uploaded images 404 in production*: serve the `media/` folder from your web server.
- *Can't get into `/manage/`*: the account needs staff status. Accounts made with `createsuperuser` have it.
- *Forgot your password*: `python manage.py changepassword <username>`.
- *Want a clean slate*: delete `db.sqlite3` and the contents of `media/`, then run `migrate` and `seed_demo_data` again.

## Where things live

- `techstore/`: settings and the root URLs.
- `account_module/`: the custom user (email login plus address), sign-up, login and account pages.
- `product_module/`: brands, categories, storage options, colors, products, versions and the public product pages.
- `site_module/`: store settings, appearance, fonts, home sections, menu, footer, text pages.
- `order_module/`: the cart and the checkout page.
- `home_module/`: the home page.
- `manager_panel/`: the `/manage/` panel.
- `templates/`, `static/`: shared templates, CSS, JavaScript and images.
- `sample_media/`: the images used by the sample data.
- `utils/`: small shared helpers (validators, file cleanup, slugs, test factories).

That's it. If you run into anything strange on first launch, tell me exactly what you see and I'll sort it out.