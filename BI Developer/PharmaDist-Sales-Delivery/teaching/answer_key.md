# פתרון ומחוון (למדריך)

## שש הבעיות
| # | קובץ | עמודה | בעיה | כמה | תיקון |
|---|---|---|---|---|---|
| 1 | OrderLines | כל העמודות | שורות כפולות לגמרי (הנתונים יוצאו פעמיים) | 437 | Remove Duplicates |
| 2 | OrderLines | Quantity | שורות עם כמות 0 | 292 | Filter `Quantity > 0` |
| 3 | Orders | CustomerID | אותיות קטנות או רווחים, כמו `c1045` | 362 הזמנות | Trim ואחריו UPPERCASE |
| 4 | Customers | Region | 20 כתיבים שונים ל-5 אזורים | 28 לקוחות | Trim ואחריו Capitalize Each Word |
| 5 | Customers | City | רווחים ואותיות קטנות (30 כתיבים ל-22 ערים) | 12 לקוחות | Trim ואחריו Capitalize Each Word |
| 6 | Products | Category | ערך ריק | 2 מוצרים | Replace Values, עם Match entire cell contents |

**בעיה מוסתרת (בונוס):** Power Query מגדיר את UnitPrice כ-Whole Number, כי הוא מנחש את הסוג לפי 200 השורות הראשונות. אם לא מתקנים, סך המכירות יוצא גבוה ב-**2,500.99 ₪**. מתקנים בצעד **Changed Type הראשון** ובוחרים `type number`.

## הצעדים המרכזיים ב-M (כמו שהם מופיעים בשורת הנוסחה)
```
// Orders
= Table.TransformColumns(#"Changed Type", {{"CustomerID", Text.Trim, type text}})
= Table.TransformColumns(#"Trimmed Text", {{"CustomerID", Text.Upper, type text}})

// Customers
= Table.TransformColumns(#"Changed Type", {{"Region", Text.Trim, type text}, {"City", Text.Trim, type text}})
= Table.TransformColumns(#"Trimmed Text", {{"Region", Text.Proper, type text}, {"City", Text.Proper, type text}})

// Products
= Table.ReplaceValue(#"Changed Type", "", "Unclassified", Replacer.ReplaceValue, {"Category"})

// OrderLines -> FACT_Sales
= Table.Distinct(#"Changed Type")
= Table.SelectRows(#"Removed Duplicates", each [Quantity] > 0)
= Table.NestedJoin(#"Filtered Rows", {"OrderID"}, Orders, {"OrderID"}, "Orders", JoinKind.LeftOuter)
= Table.AddColumn(#"Expanded Orders", "NetAmount", each [QtyDelivered] * [UnitPrice] * (1 - [DiscountPct]), type number)
```

## מספרי היעד לפי אזור (NetAmount, כל השנים)
| Region | NetAmount |
|---|---|
| Center | 44,517,335 |
| Jerusalem | 37,678,603 |
| North | 46,670,287 |
| Sharon | 12,440,329 |
| South | 38,759,618 |
| **Total** | **180,066,172** |

## מחוון הערכה (100 נקודות)
| קריטריון | נקודות | מה בודקים |
|---|---|---|
| איתור הבעיות | 30 | 5 נקודות לכל בעיה שזוהתה, כולל מספר השורות |
| תיקון ב-Power Query | 30 | כל תיקון מופיע כצעד, והסדר נכון (הסוג מתוקן בצעד שבו הוא נקבע) |
| התאמה למספרי היעד | 25 | 5 נקודות לכל שורה בטבלת היעדים |
| הסבר לקהל לא טכני | 15 | תשובה למשימת האתגר: ברורה, בלי ז'רגון, ומסבירה למה זה חשוב |
