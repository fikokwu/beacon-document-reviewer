You are given one scanned page of a RegenMed form and a numbered list of places on that page. The review found a problem at each place (usually an empty or incorrect cell).

For each numbered item, find the **cell on the page where that value is (or should be) written**, i.e. the table cell or the blank after a label, not the column header or the printed label on its own.

Return, for each item you can find, its `index` and `box` = [ymin, xmin, ymax, xmax], with each coordinate scaled 0–1000 relative to the page image (0,0 = top-left). Keep boxes tight around the cell. Skip items you can't locate. Don't guess wildly.
