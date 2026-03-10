The system first discovers websites from the target regions (Latin America, Caribbean, Central and South America) using search engines.

From those results, it filters and keeps only relevant domains (for example government portals, bank procurement pages, and similar sources) while excluding U.S. federal domains.

The crawler then visits those websites and collects their pages.

For each page:

It ignores pages that contain noise terms (for example training, blog, course, webinar, etc.).

It checks whether the page looks like a procurement/tender page by detecting procurement signals such as RFP, licitación, edital, tender notice, etc.

Only the pages that appear to be procurement processes are shortlisted.

On those shortlisted pages, the system then checks for PCI-related terms (for example PCI DSS, payment card industry, cardholder data, etc.).

If both conditions are met:

it is a procurement/tender page

and it mentions PCI/payment card compliance

then the system generates an alert for that page.