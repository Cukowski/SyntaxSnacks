# API Reference

The application provides a simple API for fetching dynamic content.

---

### `GET /api/fun`

Returns a random "fun snack" (a joke or a fact) from the `data/fun_snacks.csv` file. This is used on the home page for the "Show another" button.

**Success Response (200 OK)**

```json
{ "type": "joke", "text": "There are 10 kinds of people in the world: those who understand binary, and those who don't." }
```