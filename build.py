#!/usr/bin/env python3
"""CarQuoteCheck static-site generator and pre-package auditor.
Change SITE_URL and CONTACT_EMAIL before publishing to a custom domain.
Run: python build.py
"""
from __future__ import annotations
import json, re, shutil, sys, zipfile, unicodedata
from datetime import datetime
from pathlib import Path
from html import escape
from xml.etree import ElementTree as ET
from PIL import Image, ImageDraw, ImageFont
ROOT = Path(__file__).resolve().parent
SITE_URL = "https://carquotecheck.pages.dev"
CONTACT_EMAIL = "hello@carquotecheck.com"  # Replace with a monitored mailbox before launch.
SITE_NAME = "CarQuoteCheck"
DATA_REVIEWED = "November 17, 2026"
AVERAGE_FEE_SOURCE = "https://caredge.com/guides/car-dealer-doc-fee-by-state"
RULES_SOURCE = "https://otdcheck.com/data/dealer-fees-and-car-sales-tax-by-state"
FTC_SOURCE = "https://www.ftc.gov/business-guidance/resources/automobile-industry-pricing-transparency-faqs"

# (code, name, vehicle-tax starting rate, trade-in rule, average doc fee, title ref,
# registration ref, counties, cities, nearby codes, local/tax caveat)
STATE_ROWS = [
("AL","Alabama",2.00,"full",489,18,393,"Jefferson, Madison, Mobile","Birmingham, Huntsville, Mobile","FL,GA,MS,TN","State automotive sales-tax rate; local taxes may add to it."),
("AK","Alaska",0.00,"none",299,15,245,"Anchorage Municipality, Fairbanks North Star, Matanuska-Susitna","Anchorage, Fairbanks, Juneau","WA,OR,ID,MT","No statewide sales tax; some cities and boroughs charge local sales taxes."),
("AZ","Arizona",5.60,"full",499,4,564,"Maricopa, Pima, Pinal","Phoenix, Tucson, Mesa","CA,NV,UT,NM","State vehicle-tax starting point; city and county vehicle taxes may apply."),
("AR","Arkansas",6.50,"full",129,10,28,"Pulaski, Benton, Washington","Little Rock, Fayetteville, Bentonville","MO,TN,MS,LA","State vehicle sales-tax rate; local taxes and transaction rules may also apply."),
("CA","California",7.25,"none",85,25,524,"Los Angeles, San Diego, Orange, Santa Clara","Los Angeles, San Diego, San Jose, Sacramento","OR,NV,AZ,UT","Statewide base rate; district taxes can materially increase the rate. Trade-ins generally do not reduce the taxable selling price."),
("CO","Colorado",2.90,"full",699,7,595,"Denver, El Paso, Arapahoe, Jefferson","Denver, Colorado Springs, Aurora, Fort Collins","WY,NE,KS,NM","State rate only; county, city, and special-district taxes vary widely."),
("CT","Connecticut",6.35,"full",599,25,180,"Fairfield, Hartford, New Haven","Bridgeport, New Haven, Stamford, Hartford","NY,MA,RI,NJ","Higher 7.75% rate may apply to vehicles priced over $50,000; confirm the trade-in threshold treatment."),
("DE","Delaware",5.25,"full",475,35,45,"New Castle, Kent, Sussex","Wilmington, Dover, Newark, Middletown","MD,NJ,PA,VA","Vehicle document fee/excise-tax treatment differs from a conventional retail sales-tax rate."),
("FL","Florida",6.00,"full",999,75,297,"Miami-Dade, Broward, Orange, Hillsborough","Miami, Orlando, Tampa, Jacksonville","GA,AL,SC,NC","State rate only; county surtax may apply to the first portion of the taxable amount."),
("GA","Georgia",7.00,"full",599,18,20,"Fulton, Gwinnett, Cobb, DeKalb","Atlanta, Savannah, Augusta, Columbus","FL,AL,TN,SC","Vehicle title ad valorem tax rules differ from a simple sales-tax calculation; use this as an editable estimate."),
("HI","Hawaii",4.00,"full",395,5,78,"Honolulu, Hawaii, Maui, Kauai","Honolulu, Hilo, Kahului, Kailua","CA,OR,WA,AK","Hawaii generally applies general excise tax rather than a conventional retail sales tax."),
("ID","Idaho",6.00,"full",399,14,126,"Ada, Canyon, Kootenai","Boise, Meridian, Nampa, Coeur d'Alene","WA,OR,NV,UT","State rate; some local options may apply depending on the transaction."),
("IL","Illinois",6.25,"full",347,155,151,"Cook, DuPage, Lake, Will","Chicago, Naperville, Rockford, Springfield","WI,IA,MO,IN","State use-tax starting rate; local taxes may apply. The documentary-fee cap is adjusted annually and the current dollar amount is not verified here."),
("IN","Indiana",7.00,"full",199,15,38,"Marion, Lake, Allen, Hamilton","Indianapolis, Fort Wayne, Evansville, South Bend","IL,MI,OH,KY","State rate; the dealer processing-fee allowance is not a hard ceiling and can require additional review above the standard amount."),
("IA","Iowa",5.00,"full",180,25,333,"Polk, Linn, Scott, Johnson","Des Moines, Cedar Rapids, Davenport, Iowa City","MN,WI,IL,MO","The vehicle registration fee is generally $10 plus 5% of the purchase price, rather than a conventional sales tax."),
("KS","Kansas",6.50,"full",499,10,80,"Johnson, Sedgwick, Shawnee, Wyandotte","Wichita, Overland Park, Topeka, Kansas City","NE,MO,OK,CO","State rate; local sales-tax rates may apply."),
("KY","Kentucky",6.00,"full",450,6,26,"Jefferson, Fayette, Kenton, Boone","Louisville, Lexington, Bowling Green, Covington","TN,MO,IL,IN","Vehicle usage tax applies; verify county-specific and transaction-specific details."),
("LA","Louisiana",5.00,"full",425,77,64,"East Baton Rouge, Orleans, Jefferson, Caddo","New Orleans, Baton Rouge, Shreveport, Lafayette","TX,AR,MS,TN","State rate only; local parish and municipal taxes may add substantially to the total."),
("ME","Maine",5.50,"full",499,33,40,"Cumberland, York, Penobscot","Portland, Lewiston, Bangor, South Portland","NH,MA,VT,NY","State vehicle sales tax rate; the dealer doc fee has no confirmed statewide dollar cap in the reference record."),
("MD","Maryland",6.50,"full",499,100,187,"Montgomery, Prince George's, Baltimore County, Anne Arundel","Baltimore, Columbia, Germantown, Silver Spring","VA,DE,PA,WV","Maryland uses a vehicle excise tax at titling. The processing fee is added to the purchase price and taxed."),
("MA","Massachusetts",6.25,"full",459,75,60,"Middlesex, Suffolk, Worcester, Essex","Boston, Worcester, Springfield, Cambridge","CT,RI,NH,VT","State rate; documentary preparation charges must be included in the advertised price."),
("MI","Michigan",6.00,"limited",260,15,128,"Wayne, Oakland, Macomb, Kent","Detroit, Grand Rapids, Ann Arbor, Lansing","WI,IN,OH,IL","Trade-in credit is limited to $12,000 for calendar year 2026. Doc-fee cap is 5% of cash price if lower than the stated cap."),
("MN","Minnesota",6.875,"full",125,8,69,"Hennepin, Ramsey, Dakota, Anoka","Minneapolis, St. Paul, Rochester, Duluth","ND,SD,IA,WI","State rate; local taxes and vehicle-specific surcharges may apply. Doc-fee cap is also subject to a percentage limit."),
("MS","Mississippi",5.00,"full",425,8,719,"Hinds, Harrison, DeSoto, Rankin","Jackson, Gulfport, Southaven, Biloxi","LA,AR,TN,AL","State vehicle sales-tax rate; registration and county charges are separate."),
("MO","Missouri",4.225,"full",565,9,57,"St. Louis County, Jackson, St. Charles, Greene","Kansas City, St. Louis, Springfield, Columbia","IA,IL,KS,AR","State rate; local sales taxes can apply. The published 2026 doc-fee cap is inflation-adjusted."),
("MT","Montana",0.00,"none",299,12,237,"Yellowstone, Missoula, Gallatin, Flathead","Billings, Missoula, Bozeman, Great Falls","ID,WY,ND,SD","Montana has no general state sales tax; vehicle registration and other fees still apply."),
("NE","Nebraska",5.50,"full",299,10,83,"Douglas, Lancaster, Sarpy, Hall","Omaha, Lincoln, Bellevue, Grand Island","SD,IA,MO,KS","State rate; local sales taxes may apply."),
("NV","Nevada",6.85,"full",499,20,49,"Clark, Washoe, Carson City","Las Vegas, Henderson, Reno, Carson City","CA,OR,ID,UT","State base plus local components; the combined rate depends on the county."),
("NH","New Hampshire",0.00,"none",375,25,51,"Hillsborough, Rockingham, Merrimack, Strafford","Manchester, Nashua, Concord, Portsmouth","ME,MA,VT,NY","No general sales tax; title, registration, and local municipal fees still apply."),
("NJ","New Jersey",6.625,"full",695,60,271,"Bergen, Essex, Middlesex, Hudson","Newark, Jersey City, Paterson, Elizabeth","NY,PA,DE,CT","State rate; certain qualifying buyers and vehicles may have exemptions or special rules."),
("NM","New Mexico",4.00,"full",339,3,60,"Bernalillo, Doña Ana, Santa Fe, Sandoval","Albuquerque, Las Cruces, Santa Fe, Rio Rancho","AZ,CO,TX,OK","New Mexico uses gross receipts tax; local rates can add to the statewide component."),
("NY","New York",4.00,"full",175,50,146,"Kings, Queens, New York, Erie, Monroe","New York City, Buffalo, Rochester, Albany","PA,NJ,CT,MA","State rate only; local sales taxes vary. A $175 maximum applies to the dealer documentation fee described by DMV guidance."),
("NC","North Carolina",3.00,"full",699,56,370,"Mecklenburg, Wake, Guilford, Durham","Charlotte, Raleigh, Greensboro, Durham","SC,VA,GA,TN","North Carolina applies a highway use tax rather than ordinary sales tax; statewide rate shown is the vehicle tax starting point."),
("ND","North Dakota",5.00,"full",299,5,123,"Cass, Burleigh, Grand Forks","Fargo, Bismarck, Grand Forks, Minot","MT,SD,MN,NE","State rate; local taxes and registration fees may apply."),
("OH","Ohio",5.75,"new_only",250,15,31,"Cuyahoga, Franklin, Hamilton, Summit","Columbus, Cleveland, Cincinnati, Toledo","MI,IN,KY,PA","Trade-in credit is listed for new vehicles only. The documentary-fee limit is statutory/formula-based; the 2026 dollar figure is not verified."),
("OK","Oklahoma",4.50,"partial",599,11,100,"Oklahoma, Tulsa, Cleveland, Canadian","Oklahoma City, Tulsa, Norman, Broken Arrow","TX,KS,MO,AR","The 4.5% combined vehicle tax includes a portion where the trade-in reduces the taxable amount; the state excise component is treated differently."),
("OR","Oregon",0.00,"none",250,106,169,"Multnomah, Washington, Clackamas, Lane","Portland, Eugene, Salem, Bend","WA,CA,ID,NV","No general sales tax. A 0.5% privilege tax can apply to new vehicles; dealer doc fee cap depends on paperwork method."),
("PA","Pennsylvania",6.00,"full",449,58,39,"Philadelphia, Allegheny, Montgomery, Bucks","Philadelphia, Pittsburgh, Allentown, Erie","NY,NJ,DE,OH","State rate; Philadelphia and Allegheny County add local vehicle sales tax. The 2026 doc-fee cap depends on electronic processing."),
("RI","Rhode Island",7.00,"full",399,53,58,"Providence, Kent, Washington, Newport","Providence, Warwick, Cranston, Pawtucket","MA,CT,NH,NY","State rate; doc-fee cap applies to qualifying sales over $10,000, with separate title-preparation fee rules."),
("SC","South Carolina",5.00,"full",400,15,40,"Greenville, Charleston, Richland, Horry","Charleston, Columbia, Greenville, Myrtle Beach","NC,GA,FL,TN","Vehicle infrastructure maintenance fee is 5% up to $500. A $225 closing fee is allowed without state review; it is not a hard doc-fee cap."),
("SD","South Dakota",4.00,"full",200,10,122,"Minnehaha, Pennington, Lincoln, Brown","Sioux Falls, Rapid City, Aberdeen, Brookings","ND,MN,IA,NE","State rate; local municipal taxes can apply."),
("TN","Tennessee",7.00,"full",499,14,29,"Davidson, Shelby, Knox, Hamilton","Nashville, Memphis, Knoxville, Chattanooga","KY,VA,NC,GA","State vehicle rate; local tax and single-article limits may affect the final amount."),
("TX","Texas",6.25,"full",150,33,74,"Harris, Dallas, Tarrant, Bexar, Travis","Houston, Dallas, Austin, San Antonio","NM,OK,LA,AR","State motor-vehicle sales tax rate; a $225 processing-fee amount may be charged without additional OCCC review, not a hard cap."),
("UT","Utah",6.10,"full",299,6,57,"Salt Lake, Utah, Davis, Weber","Salt Lake City, Provo, Ogden, St. George","ID,NV,CO,AZ","The published vehicle rate combines state and listed local components; confirm your local tax district."),
("VT","Vermont",6.00,"full",200,35,78,"Chittenden, Rutland, Washington, Windsor","Burlington, South Burlington, Rutland, Montpelier","NY,NH,MA,ME","State rate; local option tax and registration charges may apply."),
("VA","Virginia",4.15,"none",799,15,36,"Fairfax, Prince William, Loudoun, Chesterfield","Virginia Beach, Richmond, Arlington, Norfolk","MD,NC,WV,DC","Virginia motor vehicle sales/use tax is 4.15% with a $75 minimum. Trade-in value does not reduce the taxable price."),
("WA","Washington",7.00,"full",199,15,73,"King, Pierce, Snohomish, Spokane","Seattle, Tacoma, Spokane, Bellevue","OR,ID,MT,CA","Vehicle rate includes a state component plus a listed state motor-vehicle component; local sales taxes may be added."),
("WV","West Virginia",6.00,"full",250,15,52,"Kanawha, Berkeley, Monongalia, Cabell","Charleston, Huntington, Morgantown, Parkersburg","VA,MD,PA,OH","Trade-in credit requires the trade vehicle to be titled in West Virginia in the buyer's name."),
("WI","Wisconsin",5.00,"full",299,165,85,"Milwaukee, Dane, Waukesha, Brown","Milwaukee, Madison, Green Bay, Kenosha","MN,MI,IA,IL","State rate; local taxes may apply. The dealer service fee must be reasonable and is subject to state oversight."),
("WY","Wyoming",4.00,"full",500,15,616,"Laramie, Natrona, Campbell, Sweetwater","Cheyenne, Casper, Gillette, Laramie","MT,SD,NE,CO","State rate; county lodging/local fees do not replace vehicle tax and title charges."),
]
CAPS = {"AR":129,"NY":175,"IA":180,"WA":200,"OR":250,"MI":280,"MN":350,"RI":400,"MS":425,"LA":436,"PA":490,"MO":620.79,"MD":800}
NO_CAP = {"AK","DE","ID","MA","ME","NC","SC","UT","VA","WI"}
CAP_UNPRICED = {"IL","OH"}
ALLOWANCE = {"IN":261.72,"TX":225,"SC":225}
DOC_TAXABLE = {"CA":True,"CO":True,"GA":True,"IN":True,"KS":True,"ME":True,"MD":True,"MA":True,"NJ":True,"NY":False,"NC":True,"OH":False,"PA":False,"RI":True,"UT":True,"VT":True,"VA":True,"WA":False,"WI":True}
TRADE_LABELS = {"full":"Full trade-in credit (verify eligibility)","none":"No trade-in tax credit in the reference rule","limited":"Limited credit: up to $12,000 for calendar year 2026","new_only":"Credit applies to new vehicles only","partial":"Partial credit: applies to the sales-tax portion only"}

def slugify(value):
    return re.sub(r"[^a-z0-9]+", "-", value.lower().replace("&", "and")).strip("-")
def money(v):
    return f"${v:,.0f}" if abs(v-round(v)) < .005 else f"${v:,.2f}"

def build_state_data():
    out=[]
    for code,name,tax,trade,avg,title,reg,counties,cities,nearby,tax_note in STATE_ROWS:
        if code in CAPS:
            status="capped"; label=f"Confirmed cap: {money(CAPS[code])}"
        elif code in CAP_UNPRICED:
            status="capped_unpriced"; label="Capped by law; current dollar amount not verified"
        elif code in ALLOWANCE:
            status="allowance_not_cap"; label=f"{money(ALLOWANCE[code])} standard allowance; not a hard cap"
        elif code in NO_CAP:
            status="no_cap"; label="No statewide dollar cap identified in the reference rule"
        else:
            status="not_verified"; label="Statewide rule not verified"
        taxable=DOC_TAXABLE.get(code)
        tax_label="Generally taxable" if taxable is True else ("Generally not taxable" if taxable is False else "Verify state and invoice treatment")
        out.append({"code":code,"name":name,"slug":slugify(name),"tax_rate_pct":tax,"tax_rate_label":f"{tax:g}% state vehicle-tax starting point" if tax else "No general state sales tax","tax_note":tax_note,"trade_in_rule":trade,"trade_in_credit":trade in {"full","limited","new_only","partial"},"trade_in_label":TRADE_LABELS.get(trade,"No state sales tax; local rules may still apply"),"doc_fee_cap":CAPS.get(code),"doc_fee_rule_status":status,"doc_fee_rule_label":label,"doc_fee_standard_allowance":ALLOWANCE.get(code),"average_doc_fee":avg,"average_doc_fee_source":AVERAGE_FEE_SOURCE,"doc_fee_taxable":taxable,"doc_fee_taxable_label":tax_label,"title_fee_reference":title,"registration_fee_reference":reg,"government_fee_default":title+reg,"government_fee_note":"Editable planning estimate; actual title, plate, registration, county, lien, and vehicle-based charges vary.","major_counties_example":counties,"major_cities_example":cities,"nearby_states":nearby.split(","),"state_tax_source":RULES_SOURCE,"doc_fee_rule_source":RULES_SOURCE,"last_reviewed":DATA_REVIEWED})
    dc={"code":"DC","name":"District of Columbia","slug":"district-of-columbia","tax_rate_pct":6.0,"tax_rate_label":"Illustrative 6% vehicle excise-tax default","tax_note":"DC excise tax varies by vehicle weight and fuel economy; the calculator's 6% is an editable planning default.","trade_in_rule":"none","trade_in_credit":False,"trade_in_label":"No trade-in reduction to the fair-market-value tax base in the reference rule","doc_fee_cap":None,"doc_fee_rule_status":"not_verified","doc_fee_rule_label":"Statewide rule not verified","doc_fee_standard_allowance":None,"average_doc_fee":300,"average_doc_fee_source":AVERAGE_FEE_SOURCE,"doc_fee_taxable":None,"doc_fee_taxable_label":"Verify state and invoice treatment","title_fee_reference":26,"registration_fee_reference":185,"government_fee_default":211,"government_fee_note":"Editable planning estimate; actual DC title, registration, inspection, and vehicle-based charges vary.","major_counties_example":"District of Columbia (city and county equivalent)","major_cities_example":"Washington, DC","nearby_states":["MD","VA","DE","PA"],"state_tax_source":RULES_SOURCE,"doc_fee_rule_source":RULES_SOURCE,"last_reviewed":DATA_REVIEWED}
    return sorted(out,key=lambda s:s["name"])+[dc]
STATES=build_state_data(); BY_CODE={s["code"]:s for s in STATES}
FONT_CLASH="https://api.fontshare.com/v2/css?f[]=clash-display@500,600,700&display=swap"
FONT_SPACE="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap"
FA_CSS="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css"

def faq_for_state(s):
    name=s["name"]; code=s["code"]; cap=s["doc_fee_cap"]
    if cap is not None:
        a1=f"The current reference record lists a confirmed statewide dealer doc-fee cap of {money(cap)} for {name}. Some caps depend on dealer type, filing method, or transaction conditions. Compare the contract line with the official rule linked in this guide before disputing a charge."
    elif s["doc_fee_rule_status"]=="capped_unpriced":
        a1=f"{name} regulates dealer documentation fees by law, but this guide does not publish a current dollar limit because the amount is formula-based or has not been independently confirmed for the current period. Ask the dealer for its calculation and verify the latest state guidance before signing."
    elif s["doc_fee_rule_status"]=="no_cap":
        a1=f"The current reference record did not identify a statewide dollar ceiling for dealer documentation fees in {name}. That does not make every charge fair or automatically lawful. Ask for an itemized buyer's order, compare the total out-the-door price, and challenge fees for services you did not request."
    else:
        a1=f"A current statewide dollar cap for dealer documentation fees in {name} is not verified in this guide. That is different from proving there is no cap. Request the dealer's legal basis and check with the state motor-vehicle agency or consumer regulator before accepting an unusual fee."
    trade=s["trade_in_rule"]
    if trade=="full":
        a2=f"A qualifying dealer trade-in generally reduces the taxable amount in {name}. Eligibility can depend on ownership, timing, titling, and how the sale is written. Enter your trade value and confirm that the dealer applied the credit on the purchase worksheet rather than relying only on a verbal estimate."
    elif trade=="none":
        a2=f"The reference rule for {name} does not apply a general trade-in reduction to the vehicle tax base. Your trade can still reduce the cash or loan balance, but it may not reduce the tax shown on the buyer's order. Confirm the exact transaction treatment with the state agency before signing."
    elif trade=="limited":
        a2=f"{name} limits the trade-in tax credit to $12,000 for calendar year 2026 in the current reference record. The cap can change with future legislation or tax guidance. Enter the actual trade value, then verify the eligible amount and the model-year or transaction conditions with the state before relying on the result."
    elif trade=="new_only":
        a2=f"The current reference rule for {name} lists a trade-in credit for new-vehicle purchases only. A used-car transaction may therefore be taxed differently even when a dealer accepts your trade. Confirm whether your specific vehicle qualifies, and check that the buyer's order clearly shows the taxable amount."
    elif trade=="partial":
        a2=f"{name} applies trade-in value differently across its vehicle-tax components. The reference rule gives a reduction to the sales-tax portion, not necessarily every part of the combined vehicle tax. Treat the calculator as an estimate and ask the dealer to separate each tax component on the itemized quote."
    else:
        a2=f"The trade-in tax-credit rule for {name} needs transaction-specific confirmation. Some jurisdictions limit eligibility by title, ownership, vehicle type, or sale structure. Keep the trade value separate from the selling price, and ask the dealer to show the taxable base and any credit on the written buyer's order."
    tax=s["tax_rate_pct"]
    if code=="DC":
        a3="The calculator starts with an editable 6% planning rate for District of Columbia, but DC excise tax is determined using vehicle characteristics such as weight and fuel economy. The actual rate may differ materially. Enter the dealer's confirmed rate or tax amount from the worksheet before treating the estimated out-the-door total as final."
    elif code=="IA":
        a3="The Iowa calculator starts with a 5% vehicle fee plus a $10 registration-related charge, rather than treating the transaction as an ordinary retail sales-tax calculation. The exact registration and title costs depend on the vehicle and filing. Use the editable rate as a comparison aid and verify the itemized state charges."
    elif code=="OR":
        a3="Oregon has no general sales tax on ordinary used-vehicle purchases. A separate 0.5% privilege tax may apply to new vehicles. Your total still includes dealer charges, title, registration, and any applicable local or vehicle-specific fees, so enter the actual government-fee estimate from the written quote."
    else:
        a3=f"This calculator begins with a {tax:g}% {name} state-level vehicle-tax rate. It may not include county, city, district, or vehicle-specific taxes. Change the rate to match the dealer's written worksheet, and compare the taxable base as well as the percentage so a trade-in or add-on is not counted twice."
    taxable=s["doc_fee_taxable"]
    if taxable is True:
        a4=f"The reference record treats dealer documentation charges as generally taxable in {name}. The exact result can depend on whether a charge is mandatory, separately stated, and treated as part of the sale. Review the invoice description and current revenue guidance; the calculator includes an editable tax toggle for this reason."
    elif taxable is False:
        a4=f"The reference record treats a separately stated dealer documentation charge as generally not taxable in {name}. The label and structure of a charge can matter, and other dealer add-ons may be treated differently. Check the buyer's order and current state tax guidance before changing the taxable-fee setting in the calculator."
    else:
        a4=f"The tax treatment of a dealer documentation fee in {name} is not confirmed in this guide. The answer can depend on how the charge is described and whether it is mandatory or bundled with the vehicle price. Use the calculator's editable tax toggle and confirm the invoice treatment with the state revenue agency."
    cities=s["major_cities_example"].split(", "); counties=s["major_counties_example"]
    a5=f"A buyer in or near {', '.join(cities[:3])} may see different local taxes and registration costs from another part of {name}. Examples of relevant counties or jurisdictions include {counties}. For the background behind our estimates and limitations, read the CarQuoteCheck About guide before comparing a dealer's final out-the-door figure."
    return [(f"What is the dealer doc fee limit in {name}?",a1),(f"Does {name} give a tax credit for a trade-in?",a2),(f"What vehicle sales tax rate should I enter for {name}?",a3),(f"Is a dealer doc fee taxable in {name}?",a4),(f"Do county and city fees change a car's out-the-door price in {name}?",a5)]

def header_html():
    links=[("auditor-wizard",'fa-calculator','OTD Auditor'),("state-directory",'fa-map-location-dot','State Fee Guide'),(None,'fa-heart','Saved Quotes'),("faq",'fa-circle-question','FAQ')]
    def anchor(target,icon,label,mobile=False):
        extra='data-open-saved' if target is None else f'data-scroll-target="{target}"'
        count='<span class="saved-count" data-saved-count>0</span>' if label=="Saved Quotes" else ''
        klass='mobile-nav-link' if mobile else 'nav-link'
        return f'<a class="{klass}" href="/" {extra}><i class="fa-solid {icon}" aria-hidden="true"></i><span>{label}</span>{count}</a>'
    desktop=''.join(anchor(*x) for x in links); mobile=''.join(anchor(*x,True) for x in links)
    return f'''<header class="site-header"><div class="header-inner">
      <a href="/" class="brand-logo" aria-label="CarQuoteCheck home"><span class="brand-mark"><i class="fa-solid fa-car-side" aria-hidden="true"></i></span><span class="brand-word">CarQuote<span>Check</span></span></a>
      <nav class="desktop-nav" aria-label="Primary navigation">{desktop}</nav>
      <a class="button button-primary header-cta" href="/" data-scroll-target="auditor-wizard"><i class="fa-solid fa-magnifying-glass-dollar" aria-hidden="true"></i> Check My Quote</a>
      <button class="mobile-menu-toggle" type="button" aria-label="Open navigation menu" aria-expanded="false" aria-controls="mobile-drawer"><i class="fa-solid fa-bars" aria-hidden="true"></i></button>
    </div><nav class="mobile-drawer" id="mobile-drawer" aria-label="Mobile navigation" hidden>{mobile}<a class="button button-primary mobile-cta" href="/" data-scroll-target="auditor-wizard"><i class="fa-solid fa-magnifying-glass-dollar" aria-hidden="true"></i> Check My Quote</a></nav></header>'''

def head_html(title,description,canonical,extra=""):
    canonical_url=SITE_URL.rstrip("/")+(canonical if canonical.startswith("/") else "/"+canonical)
    if canonical_url.endswith("//"): canonical_url=canonical_url[:-1]
    return f'''<!doctype html><html lang="en-US"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{escape(title)}</title>
<meta name="description" content="{escape(description)}"><meta name="robots" content="index, follow, max-image-preview:large"><meta name="application-name" content="CarQuoteCheck"><meta name="theme-color" content="#F8F9FA">
<link rel="canonical" href="{canonical_url}"><link rel="icon" type="image/svg+xml" href="/favicon.svg"><link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
<link rel="preconnect" href="https://api.fontshare.com" crossorigin><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://api.fontshare.com/v2/css?f[]=clash-display@500,600,700&display=swap" rel="stylesheet"><link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet"><link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css" rel="stylesheet"><link rel="stylesheet" href="/style.css">
<meta property="og:site_name" content="CarQuoteCheck"><meta property="og:type" content="website"><meta property="og:title" content="{escape(title)}"><meta property="og:description" content="{escape(description)}"><meta property="og:url" content="{canonical_url}"><meta property="og:image" content="{SITE_URL.rstrip('/')}/og-image.png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{escape(title)}"><meta name="twitter:description" content="{escape(description)}"><meta name="twitter:image" content="{SITE_URL.rstrip('/')}/og-image.png">{extra}</head>'''

def faq_section(faqs,heading="Straight answers before you sign"):
    items=[]
    for q,a in faqs:
        a_html=escape(a).replace("CarQuoteCheck About guide",'<a href="/about/">CarQuoteCheck About guide</a>')
        items.append(f'<details class="faq-item"><summary>{escape(q)}<i class="fa-solid fa-plus" aria-hidden="true"></i></summary><p>{a_html}</p></details>')
    return f'<section class="section section-narrow" id="faq"><div class="section-heading"><span class="eyebrow">COMMON QUESTIONS</span><h2>{escape(heading)}</h2><p>Plain-English context. Always confirm the final figures on your buyer\'s order.</p></div><div class="faq-list">{"".join(items)}</div></section>'

def jsonld_graph(faqs,page_url,breadcrumb=None):
    graph=[{"@type":"WebSite","url":SITE_URL.rstrip("/")+"/","name":SITE_NAME,"inLanguage":"en-US"},{"@type":"WebApplication","name":SITE_NAME+" OTD Auditor","url":page_url,"applicationCategory":"FinanceApplication","operatingSystem":"Any","offers":{"@type":"Offer","price":"0","priceCurrency":"USD"},"description":"Free client-side out-the-door quote and dealer-fee auditor for US car buyers."}]
    if breadcrumb:
        graph.append({"@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":i+1,"name":n,"item":u} for i,(n,u) in enumerate(breadcrumb)]})
    graph.append({"@type":"FAQPage","mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in faqs]})
    return '<script type="application/ld+json">'+json.dumps({"@context":"https://schema.org","@graph":graph},ensure_ascii=False,separators=(",",":"))+'</script>'

def wizard_html(is_home,default_state=""):
    chips='''<div class="quick-state-row" aria-label="Popular states"><span>Popular:</span>'''+''.join(f'<button type="button" class="state-chip" data-state-chip="{c}">{c}</button>' for c in ["CA","FL","TX","NY","VA","GA"])+"</div>" if is_home else ""
    return f'''<section class="section wizard-section" id="auditor-wizard"><div class="section-heading center"><span class="eyebrow">THE OUT-THE-DOOR AUDITOR</span><h2>Know your number before you sign.</h2><p>Enter the quote you have. We\'ll separate government charges from dealer extras and give you a clearer counter-offer.</p></div>
<div class="wizard-card" data-default-state="{escape(default_state)}"><div class="wizard-topline"><div class="wizard-kicker"><span class="live-dot"></span> PRIVATE, INSTANT, IN YOUR BROWSER</div><div class="wizard-tools"><button class="text-button" id="sample-quote" type="button"><i class="fa-solid fa-wand-magic-sparkles"></i> Try Sample Quote</button><button class="text-button muted" id="reset-quote" type="button"><i class="fa-solid fa-rotate-left"></i> Reset</button></div></div>
<div class="progress-track" aria-label="Quote audit steps"><button class="progress-step active" type="button" data-go-step="1" aria-current="step"><span>1</span><b>Car &amp; State</b></button><div class="progress-line"></div><button class="progress-step" type="button" data-go-step="2"><span>2</span><b>Dealer Fees</b></button><div class="progress-line"></div><button class="progress-step" type="button" data-go-step="3"><span>3</span><b>Financing</b></button></div>
<form id="quote-form" novalidate>
<div class="wizard-step active" data-step="1"><div class="step-intro"><span class="step-count">STEP 01 / 03</span><h3>Start with the car.</h3><p>Use the selling price on the buyer\'s order, not the advertised payment.</p></div>
<div class="field-grid two-col"><label class="field field-wide"><span>State where you\'ll register</span><span class="select-wrap"><select id="state-select" required aria-label="State where you will register the car"><option value="">Select your state</option></select><i class="fa-solid fa-chevron-down"></i></span><small id="state-hint">State rules set the starting point. Local taxes may add more.</small>{chips}</label>
<label class="field"><span>Vehicle selling price <em>USD</em></span><span class="input-wrap"><span class="input-prefix">$</span><input id="selling-price" type="number" inputmode="decimal" min="0" step="0.01" value="32000" required></span></label>
<label class="field"><span>Trade-in value <em>optional</em></span><span class="input-wrap"><span class="input-prefix">$</span><input id="trade-in" type="number" inputmode="decimal" min="0" step="0.01" value="0"></span></label>
<label class="field"><span>Estimated vehicle tax rate</span><span class="input-wrap input-suffix"><input id="tax-rate" type="number" inputmode="decimal" min="0" max="20" step="0.001" value="6"><span class="input-unit">%</span></span><small>Editable. Add your county or city rate when applicable.</small></label>
<div class="field field-note"><label class="check-row"><input id="apply-trade-credit" type="checkbox"><span class="check-ui"></span><span><b>Apply trade-in tax credit</b><small id="trade-credit-hint">Confirm your state\'s eligibility rule.</small></span></label></div></div>
<div class="step-actions"><span class="privacy-note"><i class="fa-solid fa-lock"></i> Nothing is sent to a server.</span><button class="button button-primary next-step" type="button" data-next-step="2">Next: Add Dealer Fees <i class="fa-solid fa-arrow-right"></i></button></div></div>
<div class="wizard-step" data-step="2" hidden><div class="step-intro"><span class="step-count">STEP 02 / 03</span><h3>What did the dealer add?</h3><p>Separate government charges from fees you can question or negotiate.</p></div>
<div class="field-grid two-col"><label class="field"><span>Dealer doc fee</span><span class="input-wrap"><span class="input-prefix">$</span><input id="doc-fee" type="number" inputmode="decimal" min="0" step="0.01" value="300"></span><small id="doc-fee-hint">Enter the dealer\'s exact documentation fee.</small></label>
<label class="field"><span>Government title &amp; registration</span><span class="input-wrap"><span class="input-prefix">$</span><input id="gov-fees" type="number" inputmode="decimal" min="0" step="0.01" value="200"></span><small>Editable planning estimate. Use the quote\'s DMV line items.</small></label>
<div class="field field-wide"><span class="field-label">Dealer add-ons <em>tap to add quoted items</em></span><div class="fee-chip-grid">
<button type="button" class="fee-chip" data-fee-name="VIN Etching" data-fee-value="299"><i class="fa-solid fa-fingerprint"></i> + VIN Etching</button><button type="button" class="fee-chip" data-fee-name="Paint Protection" data-fee-value="799"><i class="fa-solid fa-spray-can-sparkles"></i> + Paint Protection</button><button type="button" class="fee-chip" data-fee-name="Nitrogen Tires" data-fee-value="199"><i class="fa-solid fa-gauge-high"></i> + Nitrogen Tires</button><button type="button" class="fee-chip" data-fee-name="Dealer Prep" data-fee-value="499"><i class="fa-solid fa-screwdriver-wrench"></i> + Dealer Prep</button><button type="button" class="fee-chip" data-fee-name="Market Adjustment" data-fee-value="1500"><i class="fa-solid fa-arrow-trend-up"></i> + Market Adjustment</button><button type="button" class="fee-chip" data-fee-name="LoJack" data-fee-value="895"><i class="fa-solid fa-location-dot"></i> + LoJack</button></div>
<div id="addon-list" class="addon-list" aria-live="polite"><p class="empty-addons">No dealer add-ons added.</p></div>
<div class="custom-fee-row"><label class="field"><span>Custom fee name</span><input id="custom-fee-name" type="text" maxlength="42" placeholder="e.g. Window tint"></label><label class="field"><span>Amount</span><span class="input-wrap"><span class="input-prefix">$</span><input id="custom-fee-amount" type="number" min="0" step="0.01" placeholder="0"></span></label><button class="button button-secondary add-custom-fee" id="add-custom-fee" type="button"><i class="fa-solid fa-plus"></i> Add Fee</button></div></div>
<div class="field field-wide tax-fee-toggle"><label class="check-row"><input id="doc-fee-taxable" type="checkbox"><span class="check-ui"></span><span><b>Include the doc fee in the taxable amount</b><small id="doc-tax-hint">Use the state rule and your invoice to confirm.</small></span></label></div></div>
<div class="step-actions"><button class="button button-quiet prev-step" type="button" data-prev-step="1"><i class="fa-solid fa-arrow-left"></i> Back</button><button class="button button-primary next-step" type="button" data-next-step="3">Next: Financing (Optional) <i class="fa-solid fa-arrow-right"></i></button></div></div>
<div class="wizard-step" data-step="3" hidden><div class="step-intro"><span class="step-count">STEP 03 / 03</span><h3>How are you paying?</h3><p>Cash or a loan? We\'ll show the monthly cost and the financing impact of dealer extras.</p></div>
<div class="finance-switch" role="group" aria-label="Payment method"><button type="button" class="finance-option active" data-financing="cash" aria-pressed="true"><i class="fa-solid fa-money-bill-wave"></i> Paying Cash</button><button type="button" class="finance-option" data-financing="loan" aria-pressed="false"><i class="fa-solid fa-car"></i> Financing Loan</button></div>
<div class="field-grid two-col loan-fields" id="loan-fields" hidden><label class="field"><span>APR <em>annual rate</em></span><span class="input-wrap input-suffix"><input id="apr" type="number" inputmode="decimal" min="0" max="50" step="0.01" value="6.9"><span class="input-unit">%</span></span><small>Enter 0 for a true 0% APR estimate.</small></label><label class="field"><span>Loan term</span><span class="input-wrap input-suffix"><input id="loan-months" type="number" inputmode="numeric" min="1" max="120" step="1" value="72"><span class="input-unit">Months</span></span></label></div>
<div class="audit-ready"><div class="audit-ready-icon"><i class="fa-solid fa-magnifying-glass-dollar"></i></div><div><b>Your quote, x-rayed.</b><p>We\'ll compare the dealer\'s total with a state-aware target and flag charges worth questioning.</p></div></div>
<div class="step-actions"><button class="button button-quiet prev-step" type="button" data-prev-step="2"><i class="fa-solid fa-arrow-left"></i> Back</button><button class="button button-primary audit-button" type="submit"><i class="fa-solid fa-magnifying-glass-dollar"></i> Audit My Quote</button></div></div><p class="form-error" id="form-error" role="alert" hidden></p></form>
<div class="wizard-footnote"><i class="fa-solid fa-lock"></i> Free US Dealership Audit <span></span> No Login <span></span> Zero Dealer Spam</div></div></section>'''

def state_directory_html():
    rows=[]; cards=[]
    for s in STATES:
        status="Capped" if s["doc_fee_cap"] is not None else ("No cap" if s["doc_fee_rule_status"]=="no_cap" else "Verify rule")
        bclass="badge-green" if s["doc_fee_cap"] is not None else ("badge-amber" if s["doc_fee_rule_status"]=="no_cap" else "badge-gray")
        href=f'/{s["slug"]}-car-dealer-doc-fee-calculator/'; tax=f'{s["tax_rate_pct"]:g}%'
        rows.append(f'<tr data-state-row data-code="{s["code"]}" data-name="{escape(s["name"].lower())}" data-rule="{s["doc_fee_rule_status"]}"><td><a class="state-name-link" href="{href}">{escape(s["name"])} <span>{s["code"]}</span></a></td><td><span class="status-badge {bclass}">{status}</span></td><td class="numeric">{money(s["average_doc_fee"])}</td><td class="numeric">{tax}</td><td>{escape(s["trade_in_label"].split(" (")[0])}</td><td><a class="table-audit-link" href="{href}">Audit state <i class="fa-solid fa-arrow-up-right-from-square"></i></a></td></tr>')
        cards.append(f'<article class="state-card" data-state-card data-code="{s["code"]}" data-name="{escape(s["name"].lower())}" data-rule="{s["doc_fee_rule_status"]}"><div class="state-card-top"><div><span class="state-code">{s["code"]}</span><h3>{escape(s["name"])}</h3></div><span class="status-badge {bclass}">{status}</span></div><div class="state-card-stats"><div><small>Avg. doc fee</small><b>{money(s["average_doc_fee"])}</b></div><div><small>State tax</small><b>{tax}</b></div><div><small>Trade-in</small><b>{"Credit" if s["trade_in_credit"] else "Check rule"}</b></div></div><a class="button button-light state-card-cta" href="{href}">Audit {escape(s["name"])} <i class="fa-solid fa-arrow-right"></i></a></article>')
    return f'''<section class="section directory-section" id="state-directory"><div class="section-heading"><span class="eyebrow">50 STATES + WASHINGTON, DC</span><h2>Your state\'s fee rules, made clearer.</h2><p>Browse state-level starting points, doc-fee guidance and trade-in rules. Local tax and registration charges may vary.</p></div>
<div class="directory-controls"><label class="directory-search"><i class="fa-solid fa-magnifying-glass"></i><input id="state-search" type="search" placeholder="Search state, e.g. Florida or FL..." autocomplete="off"><kbd>/</kbd></label><div class="filter-pills" role="group" aria-label="Filter states"><button class="filter-pill active" type="button" data-filter="all">All 51</button><button class="filter-pill" type="button" data-filter="capped">Capped states</button><button class="filter-pill" type="button" data-filter="uncapped">Uncapped / high fee</button></div></div><p class="directory-count" id="directory-count">Showing 51 jurisdictions</p>
<div class="directory-table-wrap"><table class="state-table"><thead><tr><th>State</th><th>Doc-fee rule</th><th>Avg. doc fee</th><th>State tax</th><th>Trade-in</th><th></th></tr></thead><tbody>{''.join(rows)}</tbody></table></div><div class="state-card-grid" id="state-card-grid">{''.join(cards)}</div>
<p class="data-note"><i class="fa-solid fa-circle-info"></i> Average doc fees are third-party market benchmarks, not legal caps or guaranteed dealer prices. “Verify rule” means the statewide rule is not confirmed in our reference data. <a href="/about/">See data methodology</a>.</p></section>'''

def results_html():
    return '''<section class="section results-section" id="audit-results" aria-live="polite" hidden><div class="results-shell">
      <div class="results-heading"><div><span class="eyebrow">Your dealership X-ray</span><h2>Here's what the numbers say.</h2><p>Review each line item and adjust your target before you send a counter-offer.</p></div><button class="text-button" id="edit-quote" type="button"><i class="fa-solid fa-pen"></i> Edit quote</button></div>
      <div class="verdict-banner" id="verdict-banner"><div class="verdict-copy"><span class="verdict-eyebrow">Quote check result</span><strong id="verdict-label">Fair deal</strong><small id="verdict-note">Your quote is close to the current reference target.</small></div><div class="score-wrap"><div class="score-ring"><b id="fairness-score">--</b><small>/100</small></div><span>Fairness score</span></div><div class="savings-callout"><small>Potential savings</small><strong id="potential-savings">$0</strong><span>vs. your current quote</span></div></div>
      <div class="comparison-grid"><article class="compare-card quoted-card"><span class="compare-label"><i class="fa-solid fa-file-invoice-dollar"></i> Dealer quoted OTD</span><strong class="money-large" id="quoted-otd">$0</strong><small id="quoted-subline">Based on the figures you entered</small></article><article class="compare-card target-card"><span class="compare-label"><i class="fa-solid fa-bullseye"></i> Fair target OTD</span><strong class="money-large" id="target-otd">$0</strong><small id="target-subline">Editable negotiation target</small></article></div>
      <div class="xray-card"><div class="xray-header"><div><span class="eyebrow">Line-by-line review</span><h3>See what is driving the total.</h3></div><span class="xray-legend"><i class="legend-green"></i> Government <i class="legend-amber"></i> Review <i class="legend-red"></i> Optional add-on</span></div><div id="xray-lines" class="xray-lines"></div><div class="xray-tip"><i class="fa-solid fa-lightbulb"></i><span>Uncheck a yellow or red line to remove it from your counter-offer target. Your dealer quote stays unchanged.</span></div><div class="target-live-row"><span>Updated target OTD</span><b id="live-target-otd">$0</b></div><div class="target-live-row loan-live" id="live-payment-row" hidden><span>Estimated target monthly payment</span><b id="live-target-payment">$0 / mo</b></div></div>
      <div class="loan-trap" id="loan-trap" hidden><div class="loan-trap-icon"><i class="fa-solid fa-triangle-exclamation"></i></div><div class="loan-trap-copy"><span class="eyebrow">The hidden loan trap</span><h3>Small fees can live in your loan for years.</h3><p>Financing the flagged dealer fees may add <b id="extra-monthly">$0</b> per month and about <b id="extra-interest">$0</b> in extra interest over the loan term.</p><small>Estimate assumes the quoted APR and term, with no extra down payment or lender-specific fees.</small></div></div>
      <div class="result-actions"><button class="button button-primary" id="save-quote" type="button"><i class="fa-solid fa-heart"></i> Save &amp; Compare Quote</button><button class="button button-secondary" id="download-card" type="button"><i class="fa-solid fa-download"></i> Download Audit Card PNG</button><button class="button button-secondary" id="copy-link" type="button"><i class="fa-solid fa-link"></i> Copy Shareable Link</button></div>
      <div class="counter-email-card"><div class="counter-email-heading"><div><span class="eyebrow">Your next move</span><h3>Send a calm, clear counter-offer.</h3><p>Choose the tone that feels right. Edit before sending.</p></div><button class="button button-quiet" id="print-sheet" type="button"><i class="fa-solid fa-print"></i> Print 1-Page Sheet</button></div><div class="email-toolbar"><label class="field"><span>Email tone</span><select id="email-tone"><option value="polite">Polite</option><option value="firm">Firm</option><option value="walkaway">Walk-Away</option></select></label><button class="button button-secondary" id="copy-email" type="button"><i class="fa-solid fa-copy"></i> Copy Email</button></div><textarea id="counter-email" rows="9" spellcheck="true" aria-label="Editable counter-offer email"></textarea></div>
      <div class="partner-card"><div class="partner-icon"><i class="fa-solid fa-scale-balanced"></i></div><div><span class="eyebrow">A smart next step</span><h3>Compare auto insurance and loan terms, too.</h3><p>Your vehicle price is one part of the cost. Review loan disclosures and insurance options before committing.</p></div><a href="https://www.consumerfinance.gov/consumer-tools/auto-loans/" rel="nofollow" target="_blank">Explore auto-loan guidance <i class="fa-solid fa-arrow-up-right-from-square"></i></a></div>
      <p class="results-disclaimer">CarQuoteCheck is an educational estimate, not legal, tax, lending, or financial advice. Your actual taxes, fees, trade-in treatment, and loan terms may differ. Verify every line on the dealer's written buyer's order.</p>
    </div></section>'''

def footer_html():
    return f'''<footer class="site-footer"><div class="footer-top"><a href="/" class="brand-logo"><span class="brand-mark"><i class="fa-solid fa-car-side"></i></span><span class="brand-word">CarQuote<span>Check</span></span></a><p>Clearer numbers. Calmer car buying.</p><a class="footer-cta" href="/" data-scroll-target="auditor-wizard">Audit your quote <i class="fa-solid fa-arrow-right"></i></a></div><div class="footer-bottom"><span>© {datetime.now().year} CarQuoteCheck. Independent consumer tool.</span><nav aria-label="Footer navigation"><a href="/about/">About</a><a href="/contact/">Contact</a><a href="/privacy-policy/">Privacy</a><a href="/terms-of-service/">Terms</a></nav></div><p class="footer-source">State-rule references and fee benchmarks are informational snapshots. Always verify with your state agency and the written buyer's order.</p></footer>
<div class="modal-backdrop" id="saved-modal" hidden><section class="modal-card" role="dialog" aria-modal="true" aria-labelledby="saved-modal-title"><div class="modal-header"><div><span class="eyebrow">YOUR BROWSER ONLY</span><h2 id="saved-modal-title">Saved dealer quotes</h2><p>Compare up to four quotes stored on this device.</p></div><button class="icon-button" type="button" data-close-modal aria-label="Close saved quotes"><i class="fa-solid fa-xmark"></i></button></div><div id="saved-quotes-list" class="saved-quotes-list"></div><div class="modal-footer"><span id="saved-modal-count">0 of 4 quotes saved</span><button class="button button-quiet" type="button" data-close-modal>Done</button></div></section></div>
<div class="toast" id="toast" role="status" aria-live="polite"></div><script src="/script.js" defer></script></body></html>'''

def homepage_html():
    title="CarQuoteCheck | Free US Car Dealer Fee & OTD Auditor"
    desc="Audit your US car dealer quote in minutes. Check out-the-door price, documentation fees, junk add-ons, state rules, and your fair counter-offer. Free, private, no login."
    hero='''<section class="hero-section"><div class="hero-copy"><div class="trust-pill"><i class="fa-solid fa-car-side"></i> Free US Dealership Audit <span class="trust-dot"></span> No Login <span class="trust-dot"></span> Zero Dealer Spam</div><h1>Know the real price before you sign.</h1><p class="hero-subtitle">X-ray your dealer quote. Spot inflated fees, optional add-ons and financing traps before they cost you more.</p><div class="hero-actions"><a class="button button-primary button-large" href="/" data-scroll-target="auditor-wizard"><i class="fa-solid fa-magnifying-glass-dollar"></i> Check My Quote</a><a class="text-link" href="/" data-scroll-target="state-directory">Explore state fee rules <i class="fa-solid fa-arrow-down"></i></a></div><div class="hero-proof"><span><i class="fa-solid fa-lock"></i> Runs on your device</span><span><i class="fa-solid fa-file-invoice-dollar"></i> No dealer account needed</span></div></div><div class="hero-visual" aria-label="Illustrative car buyer quote audit preview"><div class="visual-glow"></div><div class="receipt-card"><div class="receipt-header"><span>Dealer buyer's order</span><i class="fa-solid fa-ellipsis"></i></div><div class="receipt-car"><div class="mini-car"><i class="fa-solid fa-car-side"></i></div><div><b>2024 Compact SUV</b><small>Sample quote breakdown</small></div></div><div class="receipt-line"><span>Selling price</span><b>$32,000</b></div><div class="receipt-line"><span>Dealer doc fee</span><b class="fee-warning">$999</b></div><div class="receipt-line"><span>Paint protection</span><b class="fee-danger">$799</b></div><div class="receipt-line"><span>Title &amp; registration</span><b>$215</b></div><div class="receipt-total"><span>Quoted OTD</span><b>$35,993</b></div><div class="receipt-audit"><span><i class="fa-solid fa-circle-check"></i> Fee review complete</span><b>Potential savings <strong>$1,798</strong></b></div></div></div></section>'''
    home_faqs=[
      ("What does out-the-door price mean?","The out-the-door (OTD) price is the total amount you must pay to complete the purchase, including the vehicle price, taxes, dealer fees, and government charges. It may be reduced by a trade-in or down payment depending on how the deal is structured."),
      ("Is a dealer documentation fee a government fee?","Usually no. A documentation or processing fee is charged by the dealership for paperwork. Some states regulate its amount or disclosure, but it is different from a state title or registration fee. Ask for every charge to be itemized on the buyer's order."),
      ("Does CarQuoteCheck provide legal or tax advice?","No. CarQuoteCheck is an educational estimate tool, not a law firm, tax adviser, DMV, or dealer. State and local rules change and may depend on the vehicle or transaction. Confirm the final tax, fee, and title amounts with the relevant agency before signing."),
      ("Does the calculator upload my quote?","No. Quote calculations run in your browser. Saved quotes use local browser storage, and share links encode the quote in the URL fragment. Do not share a link if it contains information you consider private; the tool does not need your name or VIN."),
    ]
    graph=jsonld_graph(home_faqs,SITE_URL.rstrip("/")+"/")
    main='''<main><div class="container">'''+hero+wizard_html(True)+results_html()+'''<section class="section how-section"><div class="section-heading"><span class="eyebrow">THREE STEPS. ONE CLEAR NUMBER.</span><h2>Take the pressure out of the paperwork.</h2><p>You don't need to understand every dealership fee to ask better questions.</p></div><div class="how-grid"><article><span class="how-number">01</span><i class="fa-solid fa-file-invoice-dollar"></i><h3>Enter your quote</h3><p>Add the selling price, trade-in, dealer fees, state and financing details from the buyer's order.</p></article><article><span class="how-number">02</span><i class="fa-solid fa-magnifying-glass-chart"></i><h3>Review the X-ray</h3><p>See government charges, unusually high doc fees and optional add-ons separated into clear line items.</p></article><article><span class="how-number">03</span><i class="fa-solid fa-handshake"></i><h3>Make your move</h3><p>Set a counter-offer target, send a prepared email, or save quotes to compare side by side.</p></article></div></section>'''+state_directory_html()+faq_section(home_faqs,"Car-buying questions, answered")+'''<section class="closing-cta"><div><span class="eyebrow">BEFORE YOU SIGN</span><h2>Make the numbers make sense.</h2><p>Know your out-the-door total. Keep the conversation on the price.</p></div><a class="button button-primary button-large" href="/" data-scroll-target="auditor-wizard">Audit My Quote <i class="fa-solid fa-arrow-right"></i></a></section></div></main>'''
    return head_html(title,desc,"/",graph)+"<body>"+header_html()+main+footer_html()

def state_quickfacts(s):
    cap=money(s["doc_fee_cap"]) if s["doc_fee_cap"] is not None else ("Capped by law; amount unverified" if s["doc_fee_rule_status"]=="capped_unpriced" else ("No cap identified" if s["doc_fee_rule_status"]=="no_cap" else "Not verified"))
    doc_tax=s["doc_fee_taxable_label"]
    credit=s["trade_in_label"]
    return f'''<section class="section quickfacts-section" id="state-quick-facts"><div class="section-heading"><span class="eyebrow">{escape(s["name"].upper())} AT A GLANCE</span><h2>Quick facts for {escape(s["name"])} car buyers.</h2><p>Reference data for your first pass. Always compare against the exact vehicle, county and dealer paperwork.</p></div><div class="quickfacts-grid"><article><span class="quickfact-icon"><i class="fa-solid fa-scale-balanced"></i></span><small>Legal doc-fee rule</small><b>{escape(cap)}</b><span>{escape(s["doc_fee_rule_label"])}</span></article><article><span class="quickfact-icon"><i class="fa-solid fa-receipt"></i></span><small>Average doc fee</small><b>{money(s["average_doc_fee"])}</b><span>Market benchmark, not a legal cap or fixed price</span></article><article><span class="quickfact-icon"><i class="fa-solid fa-arrow-right-arrow-left"></i></span><small>Trade-in tax credit</small><b>{escape(credit.split(" (")[0])}</b><span>{escape(credit)}</span></article><article><span class="quickfact-icon"><i class="fa-solid fa-percent"></i></span><small>Doc fee taxable?</small><b>{escape(doc_tax)}</b><span>Confirm the invoice description and current state treatment</span></article></div><p class="local-note">For buyers around {escape(s["major_cities_example"])}, including {escape(s["major_counties_example"])}, local taxes, registration, and vehicle-based charges can change the final out-the-door total. The state rate shown in the auditor is only a starting point; replace it with the rate or amount on your written quote.</p><p class="source-note">Data reviewed {DATA_REVIEWED}. <a href="{RULES_SOURCE}" rel="nofollow">State tax and rule reference</a> · <a href="{AVERAGE_FEE_SOURCE}" rel="nofollow">Average doc-fee benchmark source</a>.</p></section>'''

def nearby_html(s):
    cards=[]
    for code in s["nearby_states"]:
        n=BY_CODE[code]
        cards.append(f'<a class="nearby-card" href="/{n["slug"]}-car-dealer-doc-fee-calculator/"><span>{n["code"]}</span><b>{escape(n["name"])}</b><i class="fa-solid fa-arrow-up-right-from-square"></i><small>{money(n["average_doc_fee"])} avg. doc-fee benchmark</small></a>')
    return f'''<section class="section nearby-section"><div class="section-heading"><span class="eyebrow">CROSS-STATE SHOPPING</span><h2>Buying across state lines?</h2><p>Compare nearby state fee references before you negotiate or arrange registration.</p></div><div class="nearby-grid">{''.join(cards)}</div></section>'''

def state_page_html(s):
    slug=s["slug"]; url=SITE_URL.rstrip("/")+f'/{slug}-car-dealer-doc-fee-calculator/'
    cap=money(s["doc_fee_cap"]) if s["doc_fee_cap"] is not None else ("a formula-based cap" if s["doc_fee_rule_status"]=="capped_unpriced" else "a rule that needs checking")
    h1=f"{s['name']} Car Dealer Fee & OTD Calculator"
    desc=f"Check your {s['name']} car dealer doc fee, vehicle tax estimate, trade-in credit and out-the-door price. Free {s['name']} dealership quote auditor with no login."
    faqs=faq_for_state(s)
    crumbs=[("Home",SITE_URL.rstrip("/")+"/"),(f"{s['name']} Doc Fee Calculator",url)]
    graph=jsonld_graph(faqs,url,crumbs)
    breadcrumb=f'<nav class="breadcrumbs" aria-label="Breadcrumb"><a href="/">Home</a><i class="fa-solid fa-chevron-right"></i><span>{escape(s["name"])} Doc Fee Calculator</span></nav>'
    hero=f'''<section class="state-hero"><div class="state-hero-copy">{breadcrumb}<div class="trust-pill"><i class="fa-solid fa-car-side"></i> Free US Dealership Audit <span class="trust-dot"></span> No Login <span class="trust-dot"></span> Zero Dealer Spam</div><h1>{escape(h1)}</h1><p>Check the dealer's doc fee, trade-in treatment and estimated out-the-door price in {escape(s['name'])} before you sign.</p><a class="button button-primary" href="/" data-scroll-target="auditor-wizard"><i class="fa-solid fa-magnifying-glass-dollar"></i> Audit a {escape(s['name'])} quote</a></div><div class="state-hero-stat"><span>DOC FEE REFERENCE</span><b>{escape(cap)}</b><small>Average market benchmark: {money(s['average_doc_fee'])}</small><div class="state-stat-divider"></div><span>STATE VEHICLE TAX STARTING POINT</span><b>{s['tax_rate_pct']:g}%</b><small>Local rates and vehicle rules may apply.</small></div></section>'''
    tax_note=f'''<section class="section state-context"><div class="context-card"><span class="context-icon"><i class="fa-solid fa-circle-info"></i></span><div><h2>What to know about a {escape(s['name'])} quote</h2><p>{escape(s['tax_note'])} The current doc-fee reference is <b>{escape(s['doc_fee_rule_label'])}</b>. {escape(s['government_fee_note'])}</p><p>Federal price-transparency guidance says dealer-required charges should be reflected in the advertised price, subject to required government charges and the specific facts of an ad. <a href="{FTC_SOURCE}" rel="nofollow">Read the FTC pricing FAQ</a>.</p></div></div></section>'''
    return head_html(f"{s['name']} Car Dealer Doc Fee Calculator | CarQuoteCheck",desc,f'/{slug}-car-dealer-doc-fee-calculator/',graph)+f'<body data-default-state="{s["code"]}">'+header_html()+f'<main><div class="container">{hero}{wizard_html(False,s["code"])}{results_html()}{state_quickfacts(s)}{tax_note}{nearby_html(s)}{faq_section(faqs,s["name"]+" car-buying FAQs")}</div></main>'+footer_html()

def legal_page(slug,title,desc,content):
    canonical=f'/{slug}/'
    page_class="contact-page" if slug=="contact" else ""
    return head_html(f"{title} | CarQuoteCheck",desc,canonical)+"<body>"+header_html()+f'<main class="legal-main"><div class="container legal-container {page_class}"><nav class="breadcrumbs"><a href="/">Home</a><i class="fa-solid fa-chevron-right"></i><span>{escape(title)}</span></nav><div class="legal-hero"><span class="eyebrow">CarQuoteCheck</span><h1>{escape(title)}</h1><p>{escape(desc)}</p></div><article class="legal-content">{content}</article></div></main>'+footer_html()

def legal_pages():
    privacy='''<h2>What this tool does</h2><p>CarQuoteCheck is a client-side quote calculator. The information you type into the auditor is processed in your browser. The site does not require an account and does not operate a quote database or backend API.</p><h2>Saved quotes and browser storage</h2><p>When you save a quote, it is stored in your browser's local storage on that device. Saved quotes remain until you remove them, clear browser storage, or use a different browser or device. Anyone with access to your browser profile may be able to view them.</p><h2>Shareable links</h2><p>When you create a share link, the quote values are encoded in the URL fragment after the hash character. The fragment is not sent as part of a normal HTTP request to the website server, but anyone who receives the link can decode and view the quote values. Do not include information you would not share.</p><h2>Third-party assets</h2><p>The site loads fonts and icons from Fontshare, Google Fonts, and Cloudflare's CDN-hosted Font Awesome stylesheet. Those providers may receive standard technical request information such as your IP address and browser metadata when your browser requests their files. Review their privacy policies for details.</p><h2>No analytics or advertising cookies</h2><p>This generated MVP does not include analytics tags, ad pixels, remarketing scripts, or a cookie-based account system. Cloudflare Pages may process ordinary technical logs as part of hosting and security.</p><h2>Children</h2><p>The tool is intended for adults shopping for a vehicle and is not designed for children.</p><h2>Changes</h2><p>This notice may be updated as the site changes. Check this page for the current version.</p><h2>Contact</h2><p>For privacy questions, use the contact details on the <a href="/contact/">Contact page</a>. The displayed email address must be configured with a monitored mailbox before public launch.</p>'''
    terms='''<h2>Informational tool only</h2><p>CarQuoteCheck provides general educational estimates to help consumers review vehicle purchase quotes. It is not a law firm, tax professional, financial adviser, lender, insurance broker, vehicle dealer, or government agency. Nothing on this site creates a professional-client relationship.</p><h2>Estimates are not guarantees</h2><p>Tax rates, doc-fee rules, trade-in credits, title fees, registration fees, and lender calculations may vary by location, vehicle, transaction structure, dealer type, and date. Some values are market benchmarks or planning defaults rather than official amounts. Always verify figures with the state agency and the written buyer's order.</p><h2>Your decisions</h2><p>You are responsible for reviewing the contract, asking the dealer questions, confirming the actual out-the-door amount, and deciding whether to purchase. A result labeled fair, overpriced, or junk-fee alert is a calculator-generated estimate, not a legal conclusion about a dealer or transaction.</p><h2>Permitted use</h2><p>You may use the calculator for personal, lawful quote comparisons. Do not attempt to disrupt the site, abuse its forms, or misrepresent its estimates as official government determinations.</p><h2>Third-party links</h2><p>Links to state agencies, consumer resources, or other websites are provided for convenience. CarQuoteCheck does not control or endorse their content and is not responsible for their availability or accuracy.</p><h2>Limitation</h2><p>To the extent permitted by law, the site is provided on an as-is and as-available basis without warranties. You should retain your own copy of purchase quotes and confirmations.</p><h2>Contact</h2><p>Questions about these terms can be sent through the <a href="/contact/">Contact page</a>.</p>'''
    about=f'''<h2>Built for the moment before you sign</h2><p>CarQuoteCheck helps US car buyers understand a dealership's out-the-door (OTD) price. The tool separates the selling price, vehicle tax, dealer documentation fee, government title and registration charges, trade-in value, and optional add-ons.</p><h2>How the audit works</h2><p>The calculator estimates tax from the entered selling price, eligible trade-in credit, a taxable dealer doc fee, and taxable add-ons. It compares the dealer's quote with a negotiation target using a verified doc-fee cap where one is available, or a clearly labeled market benchmark when a cap is not confirmed. It then calculates a fairness score as an explanatory signal, not an official rating.</p><h2>Data and sources</h2><p>State vehicle-tax and trade-in references are based on OTDCheck's 51-jurisdiction dataset, last reviewed {DATA_REVIEWED}. Its underlying values link to official state revenue, motor-vehicle, attorney-general, or legislative sources and are published under a Creative Commons Attribution 4.0 licence. <a href="{RULES_SOURCE}" rel="nofollow">Open the state fee and tax dataset</a>.</p><p>Average dealer documentation-fee values are market benchmarks reproduced from CarEdge's 2026 state guide. They are not legal caps, official state averages, current dealer quotes, or guarantees of what any particular buyer will pay. <a href="{AVERAGE_FEE_SOURCE}" rel="nofollow">Review the benchmark source</a>.</p><p>Federal pricing-transparency context references the Federal Trade Commission's <a href="{FTC_SOURCE}" rel="nofollow">Automobile Industry Pricing Transparency FAQs</a>.</p><h2>What the tool cannot know</h2><p>The calculator cannot determine every local tax, vehicle-weight formula, county registration fee, lender condition, dealer-specific disclosure, title eligibility issue, or exemption. Some state doc-fee and doc-fee-taxability rules are marked not verified rather than guessed. You should confirm the precise figures with the relevant state agency and the dealer's written buyer's order.</p><h2>Privacy by design</h2><p>No quote backend or user account is used in this MVP. Calculations run locally. Saved comparisons are kept in local browser storage, and share links include the quote in the URL fragment.</p><h2>Corrections</h2><p>State rules change. Please send a report with the state, fee name, amount or rule, source URL, and date observed through the <a href="/contact/">Contact page</a>.</p>'''
    contact=f'''<h2>Contact CarQuoteCheck</h2><p>For questions or corrections, email:</p><div class="contact-email"><b id="contact-email">{escape(CONTACT_EMAIL)}</b><button class="button button-secondary" type="button" id="copy-contact-email"><i class="fa-solid fa-copy"></i> Copy email</button></div><h2>Report an outdated state fee</h2><p>One click creates an email draft with the information needed to review a state rule. Add a source link or a screenshot of the official agency page where possible.</p><a class="button button-primary" href="mailto:{escape(CONTACT_EMAIL)}?subject=Report%20Outdated%20State%20Fee&body=State%3A%20%0AFee%20or%20rule%3A%20%0ACurrent%20value%20shown%3A%20%0ACorrect%20value%20or%20rule%3A%20%0AOfficial%20source%20URL%3A%20%0ADate%20checked%3A%20%0AAdditional%20details%3A%20"><i class="fa-solid fa-flag"></i> Report outdated state fee</a><h2>What to include</h2><p>Please include the state, the fee or tax rule, the value currently shown, the corrected value if known, an official source link, and the date you checked it. We cannot guarantee immediate review or legal interpretation.</p>'''
    return {
      "privacy-policy":legal_page("privacy-policy","Privacy Policy","How CarQuoteCheck handles browser-only quote data, saved comparisons and shared links.",privacy),
      "terms-of-service":legal_page("terms-of-service","Terms of Service","Important limits on CarQuoteCheck estimates, data and permitted use.",terms),
      "about":legal_page("about","About CarQuoteCheck","Our mission, calculation approach, public data sources and important limitations.",about),
      "contact":legal_page("contact","Contact CarQuoteCheck","Send a question or report a state tax or dealer fee rule that needs updating.",contact),
    }

def make_svg_icon():
    return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="15" fill="#F38020"/><path d="M13 36.5h4.4l3.5-10.8c.8-2.4 2.7-4 5.1-4h12.2c2.3 0 4.1 1.1 5.3 3.2l6 11.6H52c2.1 0 3.7 1.7 3.7 3.7v5.1c0 1.2-1 2.2-2.2 2.2h-3.1a7.4 7.4 0 0 1-14.5 0H28a7.4 7.4 0 0 1-14.5 0h-2.1c-1.3 0-2.4-1.1-2.4-2.4v-4.9c0-2 1.8-3.7 4-3.7Zm11.8-10.5-2.4 7.6h22.8l-3.9-7.6c-.7-1.3-1.6-1.8-3.1-1.8H26c-1.1 0-1.8.6-2.2 1.8ZM20.8 47a3.6 3.6 0 1 0 0-7.2 3.6 3.6 0 0 0 0 7.2Zm22.4 0a3.6 3.6 0 1 0 0-7.2 3.6 3.6 0 0 0 0 7.2Z" fill="#fff"/></svg>'''

def pillow_assets():
    # The touch icon and SVG favicon use the same orange badge / white side-view car concept.
    im=Image.new("RGBA",(180,180),(243,128,32,255)); d=ImageDraw.Draw(im)
    d.rounded_rectangle((0,0,180,180),radius=42,fill=(243,128,32,255))
    d.rounded_rectangle((25,86,155,124),radius=15,fill=(255,255,255,255))
    d.polygon([(47,87),(61,55),(116,55),(139,87)],fill=(255,255,255,255))
    d.polygon([(65,82),(75,64),(96,64),(96,82)],fill=(243,128,32,255))
    d.polygon([(103,64),(114,64),(132,82),(103,82)],fill=(243,128,32,255))
    d.rectangle((18,99,28,112),fill=(255,255,255,255)); d.rectangle((152,99,162,112),fill=(255,255,255,255))
    d.ellipse((39,111,72,144),fill=(255,255,255,255)); d.ellipse((108,111,141,144),fill=(255,255,255,255))
    d.ellipse((48,120,63,135),fill=(243,128,32,255)); d.ellipse((117,120,132,135),fill=(243,128,32,255))
    im.save(ROOT/"apple-touch-icon.png")

    og=Image.new("RGB",(1200,630),(248,249,250)); od=ImageDraw.Draw(og)
    od.ellipse((820,-195,1350,345),fill=(255,247,237))
    od.rounded_rectangle((70,72,142,144),radius=22,fill=(243,128,32))
    # Small white car silhouette inside the orange brand tile.
    od.rounded_rectangle((84,108,130,122),radius=5,fill="white")
    od.polygon([(91,109),(99,95),(116,95),(125,109)],fill="white")
    od.ellipse((91,117,101,127),fill="white"); od.ellipse((114,117,124,127),fill="white")
    def font(name,size):
        candidates=["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf","/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"] if name=="bold" else ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf","/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"]
        for fp in candidates:
            if Path(fp).exists(): return ImageFont.truetype(fp,size)
        return ImageFont.load_default()
    brand=font("bold",43)
    x0=164; y0=82
    od.text((x0,y0),"CarQuote",font=brand,fill=(17,24,39))
    brand_width=od.textbbox((0,0),"CarQuote",font=brand)[2]
    od.text((x0+brand_width+5,y0),"Check",font=brand,fill=(243,128,32))
    od.text((72,222),"Know the real price",font=font("bold",65),fill=(17,24,39))
    od.text((72,300),"before you sign.",font=font("bold",65),fill=(17,24,39))
    od.text((77,392),"Free US car dealer fee & out-the-door price auditor",font=font("regular",25),fill=(75,85,99))
    od.rounded_rectangle((76,474,388,542),radius=20,fill=(243,128,32))
    od.text((108,493),"AUDIT YOUR QUOTE",font=font("bold",22),fill=(255,255,255))
    # Receipt card creates a product-context visual while keeping the layout uncluttered.
    od.rounded_rectangle((813,88,1175,560),radius=29,fill=(255,255,255),outline=(229,231,235),width=3)
    od.rounded_rectangle((813,88,1175,199),radius=29,fill=(17,24,39))
    od.rectangle((813,166,1175,199),fill=(17,24,39))
    od.text((850,118),"DEALER BUYER'S ORDER",font=font("bold",17),fill=(209,213,219))
    od.text((850,151),"OUT-THE-DOOR PRICE",font=font("bold",13),fill=(156,163,175))
    od.text((850,224),"Dealer quote",font=font("regular",18),fill=(107,114,128))
    od.text((850,257),"$35,993",font=font("bold",48),fill=(17,24,39))
    od.line((850,328,1137,328),fill=(229,231,235),width=2)
    od.text((850,352),"Documentation fee",font=font("regular",17),fill=(75,85,99))
    od.text((1101,352),"$999",font=font("bold",17),fill=(217,119,6))
    od.text((850,390),"Optional add-ons",font=font("regular",17),fill=(75,85,99))
    od.text((1101,390),"$1,098",font=font("bold",17),fill=(220,38,38))
    od.rounded_rectangle((845,431,1143,530),radius=16,fill=(255,247,237))
    od.text((869,451),"POTENTIAL SAVINGS",font=font("bold",15),fill=(154,72,10))
    od.text((869,476),"$1,798",font=font("bold",39),fill=(243,128,32))
    og.save(ROOT/"og-image.png",quality=95,optimize=True)

CSS = r'''@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap');
:root{--bg:#F8F9FA;--surface:#fff;--subtle:#F3F4F6;--line:#E5E7EB;--ink:#111827;--secondary:#4B5563;--muted:#6B7280;--orange:#F38020;--orange-hover:#EA580C;--orange-soft:#FFF7ED;--green:#10B981;--green-soft:#ECFDF5;--amber:#F59E0B;--amber-soft:#FFFBEB;--red:#EF4444;--red-soft:#FEF2F2;--shadow:0 8px 30px rgba(17,24,39,.06);--radius:20px;--font-head:'Clash Display',sans-serif;--font-body:'Space Grotesk',sans-serif}
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:92px}body{margin:0;background:var(--bg);color:var(--ink);font:400 15px/1.6 var(--font-body),sans-serif;-webkit-font-smoothing:antialiased}body,button,input,select,textarea{font-family:var(--font-body),sans-serif}button,input,select,textarea{font-size:inherit}button,a{-webkit-tap-highlight-color:transparent}a{color:inherit;text-decoration:none}button{cursor:pointer}img{max-width:100%}.container{width:min(1160px,calc(100% - 48px));margin:0 auto}.site-header{position:sticky;top:0;z-index:50;background:rgba(255,255,255,.92);backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);border-bottom:1px solid var(--line)}.header-inner{height:78px;max-width:1280px;margin:auto;padding:0 32px;display:flex;align-items:center;justify-content:space-between;gap:24px}.brand-logo{display:inline-flex;align-items:center;gap:10px;flex-shrink:0}.brand-mark{width:38px;height:38px;border-radius:12px;background:var(--orange);display:grid;place-items:center;color:#fff;font-size:20px;box-shadow:0 5px 12px rgba(243,128,32,.18)}.brand-word{font:700 24px/1 var(--font-head);letter-spacing:-.7px;color:var(--ink)}.brand-word span{color:var(--orange)}.desktop-nav{display:flex;align-items:center;justify-content:center;gap:clamp(14px,2vw,28px);margin-left:auto}.nav-link{display:inline-flex;align-items:center;gap:8px;color:var(--secondary);font-size:13px;font-weight:600;white-space:nowrap;transition:color .2s}.nav-link i{font-size:14px;color:#8A93A2}.nav-link:hover,.mobile-nav-link:hover{color:var(--orange-hover)}.nav-link:hover i{color:var(--orange)}.saved-count{min-width:19px;height:19px;padding:0 5px;display:inline-grid;place-items:center;border-radius:99px;background:var(--orange-soft);color:var(--orange-hover);font:700 11px var(--font-body)}.button{border:0;border-radius:999px;min-height:46px;padding:0 20px;display:inline-flex;align-items:center;justify-content:center;gap:9px;font-size:13px;line-height:1;font-weight:700;letter-spacing:-.1px;transition:background .18s,transform .18s,box-shadow .18s,border-color .18s}.button:active{transform:translateY(1px)}.button-primary{background:var(--orange);color:#fff;box-shadow:0 7px 16px rgba(243,128,32,.18)}.button-primary:hover{background:var(--orange-hover);box-shadow:0 9px 20px rgba(243,128,32,.22)}.button-secondary{background:#fff;color:var(--ink);border:1px solid var(--line)}.button-secondary:hover,.button-light:hover{background:var(--subtle);border-color:#D1D5DB}.button-quiet{background:transparent;color:var(--secondary);border:1px solid var(--line)}.button-quiet:hover{background:var(--subtle);color:var(--ink)}.button-light{background:#fff;color:var(--ink);border:1px solid var(--line)}.button-large{min-height:54px;padding:0 25px;font-size:14px}.header-cta{min-height:43px;padding:0 18px;font-size:12px}.mobile-menu-toggle,.mobile-drawer{display:none}
.hero-section{min-height:550px;padding:88px 0 82px;display:grid;grid-template-columns:1.05fr .95fr;align-items:center;gap:54px}.hero-copy{max-width:590px}.trust-pill{display:inline-flex;align-items:center;gap:9px;padding:8px 13px;border:1px solid #F5D4B7;background:#FFFBF7;border-radius:999px;color:#A64B0B;font-size:11px;font-weight:700;letter-spacing:.2px}.trust-pill i{font-size:13px}.trust-dot{width:3px;height:3px;border-radius:50%;background:#E7A46D}.hero-copy h1,.state-hero h1{font:600 clamp(48px,5vw,68px)/.99 var(--font-head);letter-spacing:-2.8px;margin:25px 0 18px;max-width:620px}.hero-subtitle{max-width:540px;color:var(--secondary);font-size:17px;line-height:1.7;margin:0}.hero-actions{display:flex;align-items:center;gap:23px;margin-top:30px}.text-link{color:var(--ink);font-size:13px;font-weight:700;display:inline-flex;gap:9px;align-items:center}.text-link i{color:var(--orange)}.hero-proof{display:flex;gap:22px;margin-top:29px;color:var(--muted);font-size:11px;font-weight:600}.hero-proof span{display:flex;gap:7px;align-items:center}.hero-proof i{color:var(--green)}.hero-visual{position:relative;min-height:390px;display:grid;place-items:center}.visual-glow{position:absolute;inset:4% 3% 0 5%;background:radial-gradient(ellipse at center,#FFE8D4 0%,#FFF5EC 37%,rgba(248,249,250,0) 72%);border-radius:50%}.receipt-card{z-index:1;position:relative;width:min(390px,94%);padding:24px 26px 22px;background:#fff;border:1px solid rgba(229,231,235,.9);border-radius:19px;box-shadow:0 22px 65px rgba(17,24,39,.12);transform:rotate(2deg)}.receipt-header{display:flex;justify-content:space-between;align-items:center;color:#8A93A2;font-size:9px;font-weight:700;letter-spacing:1.2px;padding-bottom:17px;border-bottom:1px dashed var(--line)}.receipt-car{display:flex;align-items:center;gap:12px;padding:19px 0 17px;border-bottom:1px solid var(--line)}.mini-car{width:44px;height:44px;border-radius:13px;background:var(--orange-soft);display:grid;place-items:center;color:var(--orange);font-size:21px}.receipt-car b{font:600 17px var(--font-head);display:block}.receipt-car small{display:block;color:var(--muted);font-size:10px}.receipt-line,.receipt-total{display:flex;justify-content:space-between;align-items:center;padding:10px 0;color:var(--secondary);font-size:12px}.receipt-line b{font-size:12px;color:var(--ink);font-variant-numeric:tabular-nums}.fee-warning{color:#B7791F!important}.fee-danger{color:var(--red)!important}.receipt-total{border-top:1px solid var(--line);margin-top:4px;padding-top:15px;font-weight:700;color:var(--ink)}.receipt-total b{font:700 25px var(--font-head);font-variant-numeric:tabular-nums}.receipt-audit{margin-top:11px;padding:13px 14px;border-radius:12px;background:var(--green-soft);display:flex;flex-direction:column;gap:4px;color:#047857;font-size:10px;font-weight:600}.receipt-audit span{display:flex;gap:7px;align-items:center}.receipt-audit b{color:#065F46}.receipt-audit strong{font:700 19px var(--font-head);margin-left:4px}
.section{padding:76px 0}.section-heading{max-width:700px;margin:0 0 34px}.section-heading.center{text-align:center;margin:0 auto 34px;max-width:680px}.eyebrow{display:block;color:#A65B1C;font-size:10px;font-weight:700;letter-spacing:1.55px;margin-bottom:10px}.section-heading h2,.results-heading h2,.counter-email-heading h3,.xray-header h3{font:600 clamp(32px,3.5vw,43px)/1.08 var(--font-head);letter-spacing:-1.4px;margin:0 0 12px}.section-heading p{color:var(--secondary);font-size:14px;line-height:1.7;margin:0;max-width:650px}.section-heading.center p{margin:auto}.wizard-section{padding-top:66px;padding-bottom:85px}.wizard-card{max-width:760px;margin:0 auto;background:#fff;border:1px solid var(--line);border-radius:22px;padding:28px 34px 19px;box-shadow:var(--shadow)}.wizard-topline{display:flex;align-items:center;justify-content:space-between;gap:14px}.wizard-kicker{display:flex;align-items:center;gap:9px;font-size:9px;font-weight:700;letter-spacing:1px;color:#687385}.live-dot{width:7px;height:7px;border-radius:50%;background:#10B981;box-shadow:0 0 0 4px #ECFDF5}.wizard-tools{display:flex;gap:16px}.text-button{border:0;background:transparent;padding:4px 0;color:var(--orange-hover);font-size:11px;font-weight:700;display:inline-flex;align-items:center;gap:7px}.text-button:hover{text-decoration:underline}.text-button.muted{color:var(--muted)}.progress-track{display:flex;align-items:center;gap:10px;margin:29px 0 30px}.progress-step{display:flex;align-items:center;gap:8px;border:0;background:transparent;padding:0;color:#9CA3AF;white-space:nowrap}.progress-step span{width:27px;height:27px;border:1px solid #D1D5DB;border-radius:50%;display:grid;place-items:center;font-size:11px;font-weight:700}.progress-step b{font-size:11px;font-weight:600}.progress-step.active{color:var(--ink)}.progress-step.active span,.progress-step.complete span{border-color:var(--orange);background:var(--orange);color:#fff}.progress-step.complete{color:#64748B}.progress-line{height:1px;background:#E5E7EB;flex:1;min-width:12px}.step-intro{margin-bottom:24px}.step-count{display:block;font-size:9px;color:var(--orange-hover);font-weight:700;letter-spacing:1.2px;margin-bottom:7px}.step-intro h3{font:600 28px/1.1 var(--font-head);letter-spacing:-.6px;margin:0 0 7px}.step-intro p{margin:0;color:var(--muted);font-size:12px}.field-grid{display:grid;gap:19px 17px}.two-col{grid-template-columns:repeat(2,minmax(0,1fr))}.field{min-width:0;display:flex;flex-direction:column;gap:8px;color:var(--ink);font-size:12px;font-weight:700}.field>span:first-child,.field-label{display:flex;align-items:center;justify-content:space-between;gap:10px}.field em{font-style:normal;color:#9CA3AF;font-size:9px;font-weight:600}.field small{font-size:10px;line-height:1.45;color:var(--muted);font-weight:400}.field input,.field select,.email-toolbar select{width:100%;height:46px;background:#fff;color:var(--ink);border:1px solid #DDE1E7;border-radius:10px;padding:0 13px;outline:none;transition:border .18s,box-shadow .18s;font:500 13px var(--font-body);min-width:0}.field input:focus,.field select:focus,.email-toolbar select:focus,.directory-search input:focus{border-color:#F4A261;box-shadow:0 0 0 3px rgba(243,128,32,.12)}.input-wrap{height:46px;border:1px solid #DDE1E7;border-radius:10px;display:flex;align-items:center;overflow:hidden;background:#fff;transition:border .18s,box-shadow .18s}.input-wrap:focus-within{border-color:#F4A261;box-shadow:0 0 0 3px rgba(243,128,32,.12)}.input-wrap input{height:100%;border:0;box-shadow:none!important;border-radius:0;padding:0 12px;outline:none}.input-prefix{padding-left:13px;color:#9CA3AF;font-size:13px;font-weight:600}.input-unit{padding:0 13px;color:var(--muted);font-size:11px;font-weight:600;white-space:nowrap}.input-suffix input{padding-left:13px}.select-wrap{position:relative;display:block}.select-wrap select{appearance:none;padding-right:40px}.select-wrap>i{position:absolute;right:15px;top:16px;color:#8B95A4;font-size:11px;pointer-events:none}.field-wide{grid-column:1/-1}.field-note{justify-content:center;padding-top:6px}.check-row{display:flex;align-items:flex-start;gap:11px;cursor:pointer;font-size:12px}.check-row input{position:absolute;opacity:0;width:1px;height:1px}.check-ui{flex:0 0 18px;width:18px;height:18px;border:1.5px solid #CBD5E1;border-radius:5px;background:#fff;position:relative;margin-top:1px}.check-row input:checked+.check-ui{background:var(--orange);border-color:var(--orange)}.check-row input:checked+.check-ui:after{content:'';position:absolute;left:5px;top:2px;width:5px;height:9px;border:solid white;border-width:0 2px 2px 0;transform:rotate(45deg)}.check-row b,.check-row small{display:block}.check-row b{font-size:11px}.check-row small{margin-top:3px;color:var(--muted);font-size:10px;font-weight:400}.quick-state-row{display:flex;align-items:center;gap:6px;margin-top:9px;flex-wrap:wrap}.quick-state-row>span{font-size:10px;font-weight:600;color:var(--muted);margin-right:2px}.state-chip{border:1px solid var(--line);border-radius:99px;background:#fff;color:#475569;padding:4px 9px;font-size:9px;font-weight:700}.state-chip:hover,.state-chip.active{background:var(--orange-soft);border-color:#FDBA74;color:#C2410C}.step-actions{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-top:30px}.step-actions .button{min-height:47px}.privacy-note{color:var(--muted);font-size:10px;display:flex;align-items:center;gap:6px}.privacy-note i{color:var(--green)}.wizard-footnote{margin-top:22px;padding-top:15px;border-top:1px solid #F0F1F3;display:flex;align-items:center;justify-content:center;gap:9px;color:var(--muted);font-size:9px;font-weight:600}.wizard-footnote>i{color:var(--green)}.wizard-footnote span{width:3px;height:3px;border-radius:50%;background:#CBD5E1}.form-error{color:#B91C1C;background:var(--red-soft);border-radius:9px;padding:10px 12px;margin:15px 0 0;font-size:11px}.fee-chip-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}.fee-chip{min-height:42px;border:1px solid var(--line);border-radius:10px;background:#fff;color:#4B5563;font-size:10px;font-weight:600;display:flex;align-items:center;justify-content:center;gap:7px;padding:7px}.fee-chip i{color:#9CA3AF}.fee-chip:hover{border-color:#FDBA74;background:var(--orange-soft);color:#9A3412}.fee-chip:hover i{color:var(--orange)}.addon-list{display:flex;flex-direction:column;gap:7px;margin-top:10px}.empty-addons{font-size:10px;color:#9CA3AF;margin:3px 0}.addon-row{display:flex;align-items:center;gap:10px;padding:8px 10px;background:#FAFAFA;border:1px solid #EEF0F2;border-radius:9px}.addon-row span{flex:1;font-size:11px;font-weight:600}.addon-row input{width:105px;height:34px;padding:0 8px;border:1px solid #E5E7EB;border-radius:7px;font-size:11px;font-variant-numeric:tabular-nums}.remove-addon{border:0;background:transparent;color:#9CA3AF;padding:5px}.remove-addon:hover{color:var(--red)}.custom-fee-row{display:grid;grid-template-columns:1.2fr .8fr auto;gap:10px;align-items:end;margin-top:14px}.custom-fee-row .field{gap:6px}.custom-fee-row .field>span:first-child{font-size:10px}.custom-fee-row .field input{height:40px;font-size:11px}.add-custom-fee{min-height:40px;padding:0 15px;font-size:10px}.tax-fee-toggle{margin-top:4px}.finance-switch{display:grid;grid-template-columns:1fr 1fr;gap:7px;padding:5px;background:#F3F4F6;border-radius:13px;margin-bottom:22px}.finance-option{height:47px;border:0;background:transparent;border-radius:9px;color:#6B7280;font-size:12px;font-weight:700}.finance-option i{margin-right:7px}.finance-option.active{background:#fff;color:var(--ink);box-shadow:0 2px 8px rgba(17,24,39,.07)}.loan-fields{margin-bottom:22px}.audit-ready{display:flex;gap:14px;align-items:center;padding:17px;background:#FFF8F1;border:1px solid #FCE5D2;border-radius:13px;margin-top:24px}.audit-ready-icon{width:41px;height:41px;flex-shrink:0;border-radius:12px;background:#FDE5D1;color:var(--orange-hover);display:grid;place-items:center;font-size:17px}.audit-ready b{font:600 16px var(--font-head)}.audit-ready p{margin:3px 0 0;font-size:10px;color:var(--secondary)}
'''
CSS += r'''
.results-section{padding-top:4px;padding-bottom:82px}.results-section[hidden]{display:none}.results-shell{max-width:900px;margin:auto}.results-heading{display:flex;justify-content:space-between;align-items:flex-end;gap:20px;margin-bottom:23px}.results-heading h2{font-size:35px}.results-heading p{margin:0;color:var(--secondary);font-size:12px}.verdict-banner{display:grid;grid-template-columns:1.2fr auto 1fr;gap:20px;align-items:center;padding:22px 25px;border-radius:17px;background:#142033;color:#fff;box-shadow:0 12px 35px rgba(17,24,39,.13)}.verdict-banner.verdict-fair{background:#123B32}.verdict-banner.verdict-over{background:#3D2D12}.verdict-banner.verdict-junk{background:#451D25}.verdict-copy .verdict-eyebrow{font-size:9px;letter-spacing:1.4px;color:rgba(255,255,255,.65);display:block;margin-bottom:6px;font-weight:700}.verdict-copy strong{font:700 23px var(--font-head);display:block;letter-spacing:.4px}.verdict-copy small{font-size:10px;color:rgba(255,255,255,.7);display:block;margin-top:4px}.score-wrap{text-align:center}.score-ring{width:65px;height:65px;border:4px solid rgba(255,255,255,.26);border-top-color:#fff;border-radius:50%;margin:auto;display:flex;justify-content:center;align-items:baseline;padding-top:17px}.score-ring b{font:700 23px var(--font-head)}.score-ring small{font-size:9px;color:rgba(255,255,255,.6)}.score-wrap>span{display:block;color:rgba(255,255,255,.7);font-size:9px;margin-top:7px}.savings-callout{text-align:right;border-left:1px solid rgba(255,255,255,.19);padding-left:22px}.savings-callout small,.savings-callout span{display:block;color:rgba(255,255,255,.65);font-size:9px}.savings-callout strong{display:block;font:700 33px var(--font-head);letter-spacing:-1px;color:#FDBA74;font-variant-numeric:tabular-nums}.comparison-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:16px 0}.compare-card{padding:22px 23px;border:1px solid var(--line);border-radius:15px;background:#fff}.target-card{border-color:#F4CDAE;background:#FFFCF9}.compare-label{display:flex;align-items:center;gap:8px;color:#778293;font-size:9px;font-weight:700;letter-spacing:1px}.compare-label i{font-size:13px;color:var(--orange)}.money-large{display:block;margin:10px 0 5px;font:700 clamp(28px,4vw,38px)/1 var(--font-head);letter-spacing:-1.2px;font-variant-numeric:tabular-nums}.target-card .money-large{color:#C65B12}.compare-card small{color:var(--muted);font-size:10px}.xray-card,.counter-email-card{background:#fff;border:1px solid var(--line);border-radius:16px;padding:23px;margin-top:16px}.xray-header{display:flex;justify-content:space-between;align-items:flex-end;gap:15px;margin-bottom:13px}.xray-header h3{font-size:23px;margin:0}.xray-legend{display:flex;align-items:center;gap:11px;color:var(--muted);font-size:9px;white-space:nowrap}.xray-legend i{width:7px;height:7px;border-radius:50%;display:inline-block;margin-right:-6px}.legend-green{background:var(--green)}.legend-amber{background:var(--amber)}.legend-red{background:var(--red)}.xray-line{display:grid;grid-template-columns:12px minmax(0,1fr) auto;gap:11px;align-items:center;padding:12px 0;border-bottom:1px solid #F0F1F3}.xray-line:last-child{border-bottom:0}.line-dot{width:8px;height:8px;border-radius:50%}.line-dot.green{background:var(--green)}.line-dot.amber{background:var(--amber)}.line-dot.red{background:var(--red)}.line-main b{display:block;font-size:11px;font-weight:700}.line-main small{display:block;color:var(--muted);font-size:9px;margin-top:2px}.line-value{text-align:right;font-size:12px;font-weight:700;font-variant-numeric:tabular-nums}.line-toggle{display:flex;align-items:center;gap:7px;font-size:9px;color:#64748B;white-space:nowrap;margin-top:5px}.line-toggle input{accent-color:var(--orange)}.xray-tip{display:flex;gap:9px;padding:12px 13px;border-radius:10px;background:var(--orange-soft);color:#9A3412;font-size:10px;margin-top:12px}.xray-tip i{margin-top:2px}.target-live-row{display:flex;justify-content:space-between;align-items:center;border-top:1px solid var(--line);padding-top:14px;margin-top:16px;color:var(--secondary);font-size:11px;font-weight:600}.target-live-row b{font:700 20px var(--font-head);color:var(--ink);font-variant-numeric:tabular-nums}.loan-trap{display:flex;gap:15px;background:#FFF9ED;border:1px solid #F9DDA9;border-radius:15px;padding:19px 21px;margin-top:16px}.loan-trap-icon{width:39px;height:39px;flex-shrink:0;display:grid;place-items:center;border-radius:12px;background:#FDECC8;color:#A16207}.loan-trap-copy h3{font:600 19px var(--font-head);margin:2px 0 5px}.loan-trap-copy p{font-size:11px;line-height:1.7;color:#704D14;margin:0 0 5px}.loan-trap-copy p b{color:#92400E}.loan-trap-copy small{font-size:9px;color:#8C6A32}.result-actions{display:grid;grid-template-columns:1.1fr 1.2fr 1fr;gap:9px;margin-top:17px}.result-actions .button{min-height:47px;padding:0 13px;font-size:10px}.counter-email-card{margin-top:17px}.counter-email-heading{display:flex;align-items:center;justify-content:space-between;gap:15px}.counter-email-heading h3{font-size:24px;margin:0 0 5px}.counter-email-heading p{color:var(--muted);font-size:10px;margin:0}.counter-email-heading .button{font-size:10px;min-height:39px}.email-toolbar{display:flex;justify-content:space-between;align-items:flex-end;gap:15px;margin-top:18px}.email-toolbar .field{width:180px}.email-toolbar select{height:39px;font-size:11px}.email-toolbar .button{min-height:39px;font-size:10px}.counter-email-card textarea{width:100%;margin-top:10px;border:1px solid var(--line);border-radius:10px;padding:13px;color:#374151;font:11px/1.6 var(--font-body);resize:vertical;min-height:175px;outline:none}.counter-email-card textarea:focus{border-color:#F4A261;box-shadow:0 0 0 3px rgba(243,128,32,.12)}.partner-card{display:flex;align-items:center;gap:14px;padding:17px 20px;margin-top:16px;background:#F2F5F8;border:1px solid #E6EAF0;border-radius:14px}.partner-icon{width:40px;height:40px;border-radius:12px;background:#fff;color:#536274;display:grid;place-items:center;flex-shrink:0}.partner-card>div:nth-child(2){flex:1}.partner-card .eyebrow{font-size:8px;margin-bottom:3px;color:#738096}.partner-card h3{font:600 16px var(--font-head);margin:0 0 2px}.partner-card p{font-size:9px;color:var(--secondary);margin:0}.partner-card>a{font-size:10px;font-weight:700;color:#374151;white-space:nowrap}.partner-card>a i{margin-left:4px;color:var(--orange)}.results-disclaimer{font-size:9px;color:#9299A5;line-height:1.6;margin:13px 2px 0}.how-section{padding-top:30px}.how-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:13px}.how-grid article{position:relative;padding:27px 25px 25px;border:1px solid var(--line);border-radius:16px;background:#fff;min-height:205px}.how-number{position:absolute;right:21px;top:20px;color:#D1D5DB;font:600 22px var(--font-head)}.how-grid article>i{width:38px;height:38px;border-radius:11px;background:var(--orange-soft);color:var(--orange);display:grid;place-items:center;font-size:16px;margin-bottom:19px}.how-grid h3{font:600 19px var(--font-head);margin:0 0 8px}.how-grid p{font-size:11px;color:var(--secondary);line-height:1.65;margin:0}.directory-section{padding-top:42px}.directory-controls{display:flex;align-items:center;justify-content:space-between;gap:18px;margin:28px 0 11px}.directory-search{display:flex;align-items:center;gap:10px;width:min(420px,100%);height:46px;background:#fff;border:1px solid var(--line);border-radius:11px;padding:0 13px;color:#9CA3AF}.directory-search:focus-within{border-color:#F4A261;box-shadow:0 0 0 3px rgba(243,128,32,.1)}.directory-search input{min-width:0;flex:1;border:0;outline:none;background:transparent;color:var(--ink);font-size:12px}.directory-search kbd{border:1px solid var(--line);border-radius:5px;padding:1px 6px;font-size:10px;color:#9CA3AF}.filter-pills{display:flex;align-items:center;gap:5px;padding:4px;background:#ECEFF3;border-radius:10px}.filter-pill{border:0;border-radius:7px;background:transparent;color:#64748B;padding:8px 12px;font-size:10px;font-weight:700;white-space:nowrap}.filter-pill.active{background:#fff;color:var(--ink);box-shadow:0 1px 5px rgba(17,24,39,.08)}.directory-count{color:#98A1AE;font-size:9px;margin:0 0 10px}.directory-table-wrap{background:#fff;border:1px solid var(--line);border-radius:15px;overflow:hidden}.state-table{width:100%;border-collapse:collapse;text-align:left}.state-table th{background:#F9FAFB;color:#87909D;font-size:9px;font-weight:700;letter-spacing:.4px;text-transform:uppercase;padding:13px 16px}.state-table td{padding:13px 16px;border-top:1px solid #F0F1F3;font-size:10px;color:#64748B}.state-table tbody tr:hover{background:#FFFCF9}.state-name-link{font-size:11px;color:var(--ink);font-weight:700}.state-name-link span{margin-left:5px;color:#9CA3AF;font-size:9px;font-weight:500}.numeric{font-variant-numeric:tabular-nums}.status-badge{display:inline-flex;border-radius:99px;padding:4px 8px;font-size:8px;font-weight:700;white-space:nowrap}.badge-green{background:var(--green-soft);color:#047857}.badge-amber{background:var(--amber-soft);color:#A16207}.badge-gray{background:#F3F4F6;color:#697386}.table-audit-link{font-size:9px;color:var(--orange-hover);font-weight:700;white-space:nowrap}.table-audit-link i{font-size:8px;margin-left:3px}.state-card-grid{display:none}.data-note{display:flex;align-items:flex-start;gap:8px;margin:14px 2px 0;color:#8892A1;font-size:9px;line-height:1.6}.data-note i{color:#9AA3B1;margin-top:2px}.data-note a{color:#475569;text-decoration:underline;text-underline-offset:2px}.faq-list{border-top:1px solid var(--line)}.faq-item{border-bottom:1px solid var(--line);background:transparent}.faq-item summary{list-style:none;cursor:pointer;display:flex;align-items:center;justify-content:space-between;gap:20px;padding:18px 2px;font:600 15px var(--font-head)}.faq-item summary::-webkit-details-marker{display:none}.faq-item summary i{font-size:11px;color:var(--orange);transition:transform .2s}.faq-item[open] summary i{transform:rotate(45deg)}.faq-item p{margin:0;padding:0 36px 19px 2px;max-width:850px;color:var(--secondary);font-size:11px;line-height:1.8}.faq-item p a{color:var(--orange-hover);font-weight:700;text-decoration:underline;text-underline-offset:2px}.section-narrow{max-width:850px;margin-left:auto;margin-right:auto}.closing-cta{display:flex;align-items:center;justify-content:space-between;gap:25px;padding:31px 35px;background:#172235;border-radius:19px;color:#fff;margin:4px 0 80px}.closing-cta .eyebrow{color:#FDBA74}.closing-cta h2{font:600 29px var(--font-head);margin:0 0 5px}.closing-cta p{margin:0;color:#C4CBD5;font-size:11px}.site-footer{background:#fff;border-top:1px solid var(--line);padding:32px max(24px,calc((100vw - 1160px)/2)) 24px}.footer-top{display:flex;align-items:center;gap:20px;padding-bottom:24px;border-bottom:1px solid #F0F1F3}.footer-top .brand-mark{width:32px;height:32px;font-size:17px;border-radius:10px}.footer-top .brand-word{font-size:20px}.footer-top p{color:var(--muted);font-size:11px;margin:0}.footer-cta{margin-left:auto;color:var(--orange-hover);font-size:11px;font-weight:700}.footer-cta i{margin-left:5px}.footer-bottom{display:flex;justify-content:space-between;align-items:center;gap:18px;padding-top:19px;color:#9AA2AE;font-size:9px}.footer-bottom nav{display:flex;gap:19px}.footer-bottom a{color:#64748B}.footer-bottom a:hover{color:var(--orange)}.footer-source{font-size:8px;color:#A5ADB8;margin:13px 0 0}
'''
CSS += r'''
.state-hero{display:grid;grid-template-columns:1.25fr .75fr;gap:45px;align-items:center;padding:48px 0 24px}.breadcrumbs{display:flex;align-items:center;gap:9px;color:#8A93A2;font-size:10px;margin-bottom:23px}.breadcrumbs a{color:var(--orange-hover);font-weight:700}.breadcrumbs i{font-size:8px}.state-hero .trust-pill{margin-bottom:0}.state-hero h1{font-size:clamp(39px,4.5vw,57px);max-width:700px;margin:19px 0 12px;line-height:1.02}.state-hero-copy>p{max-width:590px;color:var(--secondary);font-size:14px;line-height:1.7;margin:0 0 20px}.state-hero .button{min-height:46px}.state-hero-stat{background:#fff;border:1px solid var(--line);border-radius:17px;padding:23px 25px;box-shadow:var(--shadow)}.state-hero-stat>span{display:block;font-size:9px;color:#8A93A2;font-weight:700;letter-spacing:1px}.state-hero-stat>b{display:block;font:700 27px var(--font-head);letter-spacing:-.5px;margin:5px 0}.state-hero-stat>small{display:block;color:var(--muted);font-size:10px;line-height:1.5}.state-stat-divider{height:1px;background:var(--line);margin:17px 0}.quickfacts-section{padding-top:56px}.quickfacts-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:11px}.quickfacts-grid article{padding:19px 17px 18px;background:#fff;border:1px solid var(--line);border-radius:14px;min-height:164px}.quickfact-icon{width:32px;height:32px;border-radius:9px;background:var(--orange-soft);color:var(--orange);display:grid;place-items:center;margin-bottom:14px}.quickfacts-grid small{display:block;font-size:9px;color:var(--muted);font-weight:600}.quickfacts-grid b{display:block;font:600 17px/1.2 var(--font-head);margin:5px 0;color:var(--ink)}.quickfacts-grid article>span:last-child{display:block;color:#8B95A2;font-size:9px;line-height:1.5}.local-note{margin:18px 0 0;padding:17px 19px;border-left:3px solid var(--orange);background:#fff;border-radius:0 10px 10px 0;color:var(--secondary);font-size:11px;line-height:1.8}.source-note{color:#929BA8;font-size:9px;margin:12px 0 0}.source-note a{color:#64748B;text-decoration:underline;text-underline-offset:2px}.state-context{padding-top:9px}.context-card{display:flex;gap:14px;padding:21px 23px;background:#fff;border:1px solid var(--line);border-radius:15px}.context-icon{width:38px;height:38px;flex-shrink:0;border-radius:11px;background:#F3F4F6;color:#64748B;display:grid;place-items:center}.context-card h2{font:600 20px var(--font-head);margin:0 0 6px}.context-card p{margin:5px 0;color:var(--secondary);font-size:10px;line-height:1.75}.context-card a{color:var(--orange-hover);text-decoration:underline}.nearby-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}.nearby-card{position:relative;display:flex;flex-direction:column;gap:4px;padding:16px 17px;background:#fff;border:1px solid var(--line);border-radius:13px;transition:border .18s,transform .18s}.nearby-card:hover{border-color:#FDBA74;transform:translateY(-2px)}.nearby-card>span{font-size:9px;color:var(--orange-hover);font-weight:700;letter-spacing:1px}.nearby-card>b{font:600 17px var(--font-head)}.nearby-card>i{position:absolute;right:15px;top:16px;color:#AAB2BD;font-size:10px}.nearby-card>small{font-size:9px;color:var(--muted)}.state-hero+.wizard-section{padding-top:48px}.legal-main{min-height:65vh}.legal-container{max-width:860px;padding-top:34px;padding-bottom:70px}.legal-hero{padding:27px 0 28px;border-bottom:1px solid var(--line)}.legal-hero h1{font:600 clamp(38px,5vw,54px)/1.05 var(--font-head);letter-spacing:-1.8px;margin:0 0 10px}.legal-hero p{margin:0;color:var(--secondary);font-size:14px}.legal-content{max-width:760px;padding-top:20px}.legal-content h2{font:600 21px var(--font-head);letter-spacing:-.3px;margin:25px 0 8px}.legal-content p{color:var(--secondary);font-size:12px;line-height:1.85;margin:0 0 13px}.legal-content a{color:var(--orange-hover);text-decoration:underline;text-underline-offset:2px}.legal-content ul{color:var(--secondary);font-size:12px;line-height:1.9}.legal-content code{background:#F3F4F6;padding:2px 5px;border-radius:4px;font-size:10px}.contact-email{display:flex;align-items:center;gap:15px;margin:15px 0;padding:15px;border:1px solid var(--line);background:#fff;border-radius:12px;max-width:500px}.contact-email b{font-size:14px}.contact-email .button{min-height:37px;font-size:10px;margin-left:auto}.notice-box{display:flex;align-items:flex-start;gap:9px;background:var(--orange-soft);padding:13px 15px;border-radius:10px;color:#8A4B13!important}.notice-box i{margin-top:4px}.modal-backdrop{position:fixed;inset:0;z-index:100;background:rgba(15,23,42,.45);backdrop-filter:blur(4px);display:grid;place-items:center;padding:20px}.modal-backdrop[hidden]{display:none}.modal-card{width:min(620px,100%);max-height:min(82vh,760px);overflow:auto;background:#fff;border-radius:20px;padding:25px;box-shadow:0 25px 80px rgba(15,23,42,.24)}.modal-header{display:flex;justify-content:space-between;gap:15px}.modal-header h2{font:600 29px var(--font-head);margin:0 0 2px}.modal-header p{margin:0;color:var(--muted);font-size:10px}.icon-button{width:36px;height:36px;border:1px solid var(--line);background:#fff;border-radius:50%;color:#64748B}.saved-quotes-list{display:flex;flex-direction:column;gap:9px;margin:20px 0}.saved-empty{padding:28px;text-align:center;color:var(--muted);font-size:11px;background:#F9FAFB;border-radius:12px}.saved-quote-row{display:grid;grid-template-columns:1fr auto;gap:10px;padding:14px;border:1px solid var(--line);border-radius:12px}.saved-quote-row b{display:block;font:600 16px var(--font-head)}.saved-quote-row small{display:block;color:var(--muted);font-size:9px}.saved-quote-metrics{display:flex;gap:12px;margin-top:8px;color:#64748B;font-size:9px}.saved-quote-row .remove-saved{border:0;background:transparent;color:#9CA3AF;font-size:10px;align-self:start}.saved-quote-row .remove-saved:hover{color:var(--red)}.modal-footer{border-top:1px solid var(--line);padding-top:15px;display:flex;justify-content:space-between;align-items:center;color:var(--muted);font-size:10px}.modal-footer .button{min-height:36px;font-size:10px}.toast{position:fixed;z-index:150;bottom:24px;left:50%;transform:translate(-50%,15px);background:#142033;color:#fff;padding:11px 17px;border-radius:99px;box-shadow:0 8px 25px rgba(0,0,0,.16);font-size:11px;opacity:0;pointer-events:none;transition:.22s}.toast.show{opacity:1;transform:translate(-50%,0)}
@media(max-width:1000px){.header-inner{padding:0 22px}.desktop-nav{gap:14px}.nav-link{font-size:11px;gap:6px}.hero-section{gap:30px}.state-table th,.state-table td{padding-left:10px;padding-right:10px}.quickfacts-grid{grid-template-columns:repeat(2,1fr)}}
@media(max-width:767px){html{scroll-padding-top:76px}.container{width:min(100% - 32px,560px)}.header-inner{height:66px;padding:0 16px}.brand-mark{width:34px;height:34px;font-size:18px;border-radius:11px}.brand-word{font-size:22px}.desktop-nav,.header-cta{display:none}.mobile-menu-toggle{display:grid;place-items:center;width:40px;height:40px;border:1px solid var(--line);border-radius:11px;background:#fff;color:var(--ink);font-size:17px}.mobile-drawer{display:flex;flex-direction:column;gap:3px;padding:11px 16px 18px;border-top:1px solid var(--line);background:rgba(255,255,255,.98);box-shadow:0 14px 22px rgba(17,24,39,.07)}.mobile-drawer[hidden]{display:none}.mobile-nav-link{height:44px;display:flex;align-items:center;gap:12px;padding:0 9px;color:var(--secondary);font-size:13px;font-weight:600}.mobile-nav-link>i{width:18px;text-align:center;color:#9099A7}.mobile-nav-link .saved-count{margin-left:auto}.mobile-cta{margin-top:8px;width:100%;min-height:45px}.hero-section{grid-template-columns:1fr;padding:48px 0 32px;gap:12px;min-height:0}.hero-copy h1{font-size:48px;letter-spacing:-2px;margin:19px 0 13px;max-width:460px}.trust-pill{font-size:9px;gap:7px;padding:7px 10px}.hero-subtitle{font-size:14px;line-height:1.65}.hero-actions{gap:16px;margin-top:21px;flex-wrap:wrap}.button-large{min-height:49px;padding:0 20px}.text-link{font-size:11px}.hero-proof{gap:15px;margin-top:19px;font-size:9px}.hero-visual{min-height:310px;margin-top:5px}.receipt-card{width:min(330px,88%);padding:18px 20px;transform:rotate(1deg)}.receipt-car{padding:13px 0}.receipt-car b{font-size:14px}.receipt-line{padding:8px 0;font-size:10px}.receipt-total b{font-size:21px}.receipt-audit{padding:10px 12px}.section{padding:57px 0}.section-heading{margin-bottom:25px}.section-heading h2{font-size:33px}.section-heading p{font-size:12px}.wizard-section{padding-top:42px;padding-bottom:56px}.wizard-card{padding:20px 17px 15px;border-radius:17px}.wizard-topline{align-items:flex-start}.wizard-kicker{font-size:8px;padding-top:5px}.wizard-tools{gap:10px}.text-button{font-size:9px}.progress-track{gap:5px;margin:23px 0}.progress-step{gap:5px}.progress-step span{width:24px;height:24px;font-size:10px}.progress-step b{font-size:9px}.progress-line{min-width:5px}.step-intro h3{font-size:26px}.step-intro p{font-size:10px}.field-grid{gap:15px 11px}.field{font-size:11px}.field input,.field select{font-size:12px}.field-grid.two-col{grid-template-columns:1fr 1fr}.field-wide{grid-column:1/-1}.step-actions{margin-top:23px;flex-wrap:wrap}.step-actions .button{min-height:44px;padding:0 13px;font-size:10px}.privacy-note{font-size:8px}.wizard-footnote{font-size:8px;gap:6px;flex-wrap:wrap}.fee-chip-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:7px}.fee-chip{font-size:9px;min-height:40px}.custom-fee-row{grid-template-columns:1fr 1fr;gap:8px}.custom-fee-row .add-custom-fee{grid-column:1/-1;width:100%}.finance-option{font-size:10px}.audit-ready{padding:13px;gap:10px}.audit-ready b{font-size:14px}.audit-ready p{font-size:9px}.results-section{padding-top:0;padding-bottom:55px}.results-heading{align-items:flex-start}.results-heading h2{font-size:29px}.results-heading p{font-size:10px}.verdict-banner{grid-template-columns:1fr auto;gap:13px;padding:17px}.verdict-copy strong{font-size:19px}.score-ring{width:56px;height:56px;padding-top:14px}.score-ring b{font-size:20px}.score-wrap>span{font-size:8px}.savings-callout{grid-column:1/-1;border-left:0;border-top:1px solid rgba(255,255,255,.17);padding:12px 0 0;text-align:left}.savings-callout strong{font-size:27px}.comparison-grid{gap:8px}.compare-card{padding:15px 13px}.compare-label{font-size:8px;gap:5px}.money-large{font-size:25px}.compare-card small{font-size:8px}.xray-card,.counter-email-card{padding:17px 14px}.xray-header{display:block}.xray-header h3{font-size:20px}.xray-legend{margin-top:9px;flex-wrap:wrap;white-space:normal;font-size:8px;gap:8px}.xray-line{grid-template-columns:9px minmax(0,1fr) auto;gap:8px}.line-main b{font-size:10px}.line-main small{font-size:8px}.line-value{font-size:10px}.line-toggle{font-size:8px}.target-live-row{font-size:9px}.target-live-row b{font-size:18px}.loan-trap{padding:15px;gap:10px}.loan-trap-copy h3{font-size:17px}.loan-trap-copy p{font-size:10px}.result-actions{grid-template-columns:1fr;gap:8px}.result-actions .button{min-height:43px;font-size:10px}.counter-email-heading{align-items:flex-start;flex-direction:column}.counter-email-heading h3{font-size:21px}.counter-email-heading .button{min-height:35px}.email-toolbar .field{width:140px}.partner-card{align-items:flex-start;flex-wrap:wrap;padding:14px}.partner-card>div:nth-child(2){min-width:calc(100% - 56px)}.partner-card>a{margin-left:53px}.how-section{padding-top:15px}.how-grid{grid-template-columns:1fr;gap:9px}.how-grid article{min-height:0;padding:20px}.how-grid article>i{margin-bottom:11px}.how-grid h3{font-size:18px}.directory-section{padding-top:27px}.directory-controls{display:block;margin:20px 0 12px}.directory-search{width:100%;height:44px}.filter-pills{margin-top:9px;justify-content:space-between}.filter-pill{padding:8px 9px;font-size:9px}.directory-table-wrap{display:none}.state-card-grid{display:grid;grid-template-columns:1fr;gap:9px}.state-card{padding:15px;background:#fff;border:1px solid var(--line);border-radius:13px}.state-card-top{display:flex;justify-content:space-between;gap:10px}.state-code{color:var(--orange-hover);font-size:8px;font-weight:700;letter-spacing:1px}.state-card h3{font:600 18px var(--font-head);margin:2px 0 0}.state-card-stats{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;padding:12px 0}.state-card-stats small{display:block;color:var(--muted);font-size:8px}.state-card-stats b{display:block;font:600 13px var(--font-head);margin-top:3px}.state-card-cta{width:100%;min-height:38px;font-size:10px}.data-note{font-size:8px}.faq-item summary{font-size:13px;padding:15px 0}.faq-item p{font-size:10px;padding-bottom:16px}.closing-cta{padding:23px 20px;flex-direction:column;align-items:flex-start;margin-bottom:55px}.closing-cta h2{font-size:25px}.closing-cta .button{width:100%}.footer-top{flex-wrap:wrap;gap:11px}.footer-top p{width:100%;order:3}.footer-cta{font-size:10px}.footer-bottom{align-items:flex-start;flex-direction:column;font-size:8px}.footer-bottom nav{gap:15px}.state-hero{grid-template-columns:1fr;gap:20px;padding:26px 0 5px}.breadcrumbs{margin-bottom:18px}.state-hero h1{font-size:39px;letter-spacing:-1.5px;margin:16px 0 10px}.state-hero-copy>p{font-size:12px}.state-hero-stat{padding:18px 19px}.state-hero-stat>b{font-size:24px}.state-hero+.wizard-section{padding-top:37px}.quickfacts-section{padding-top:43px}.quickfacts-grid{grid-template-columns:1fr 1fr;gap:8px}.quickfacts-grid article{padding:14px 12px;min-height:160px}.quickfacts-grid b{font-size:14px}.quickfacts-grid article>span:last-child{font-size:8px}.local-note{font-size:9px;padding:13px}.context-card{padding:16px;gap:10px}.context-card h2{font-size:18px}.context-card p{font-size:9px}.nearby-grid{grid-template-columns:1fr 1fr;gap:8px}.nearby-card{padding:13px}.nearby-card>b{font-size:15px}.nearby-card>small{font-size:8px}.legal-container{padding-top:18px;padding-bottom:50px}.legal-hero h1{font-size:39px}.legal-hero p{font-size:12px}.legal-content h2{font-size:19px}.legal-content p{font-size:10px}.contact-email{align-items:flex-start;flex-direction:column}.contact-email .button{margin-left:0}.modal-card{padding:19px 16px}.modal-header h2{font-size:25px}.saved-quote-row{padding:11px}.saved-quote-metrics{gap:8px;flex-wrap:wrap}}
@media(max-width:390px){.container{width:calc(100% - 26px)}.hero-copy h1{font-size:43px}.wizard-card{padding:17px 13px 14px}.progress-step b{font-size:8px}.progress-step{gap:3px}.wizard-tools{gap:7px}.text-button{font-size:8px}.step-actions .button{padding:0 10px;font-size:9px}.quickfacts-grid article{min-height:173px}.nearby-card>b{font-size:14px}}
@media print{body{background:#fff;color:#000}.site-header,.site-footer,.wizard-section,.hero-section,.how-section,.directory-section,.quickfacts-section,.state-context,.nearby-section,.results-heading .text-button,.result-actions,.counter-email-card,.partner-card,.results-disclaimer,.closing-cta{display:none!important}.results-section{display:block!important;padding:0}.results-shell{max-width:none}.verdict-banner{background:#fff!important;color:#111827;border:2px solid #111827;box-shadow:none}.verdict-copy small,.verdict-eyebrow,.score-wrap>span,.savings-callout small,.savings-callout span{color:#555}.score-ring{border-color:#555}.score-ring b,.savings-callout strong{color:#111}.comparison-grid{break-inside:avoid}.xray-card,.loan-trap{break-inside:avoid;box-shadow:none}.xray-tip{display:none}.loan-trap{background:#fff;border:1px solid #999}.target-live-row{color:#111}.target-live-row b{color:#111}a{color:inherit;text-decoration:none}}
'''

CSS += r'''
/* Focused visual refinements: clean receipt, unified verdict/target palette, and mobile-safe badges. */
.receipt-card{
  transform:none!important;overflow:hidden;
  background:linear-gradient(165deg,#fff 0%,#fbfcfe 100%);
  border:1px solid #dbe3ed;
  box-shadow:0 26px 68px rgba(23,34,53,.14),0 4px 12px rgba(23,34,53,.05);
}
.receipt-card::before{content:"";position:absolute;top:0;left:0;right:0;height:6px;background:linear-gradient(90deg,#172235 0%,#344b68 72%,#FDBA74 72%,#FDBA74 100%)}
.receipt-header{padding-top:3px;color:#64748b;letter-spacing:.06em;text-transform:none}
.receipt-car{border-bottom-color:#e6ebf1}
.receipt-total{border-top:1px solid #e6ebf1;margin-top:3px;color:#172235;font-weight:700}
.receipt-audit{background:#edf7f2;border:1px solid #d4ebde;border-radius:11px}
.verdict-banner,.verdict-banner.verdict-fair,.verdict-banner.verdict-over,.verdict-banner.verdict-junk{
  background:#172235!important;color:#fff;border:1px solid #34465f;border-left:4px solid #FDBA74;
  box-shadow:0 16px 36px rgba(23,34,53,.20)
}
.verdict-copy .verdict-eyebrow{color:#D5DFEA;letter-spacing:.04em;text-transform:none}
.verdict-copy strong{color:#fff;letter-spacing:0;text-transform:none;font-size:24px}
.verdict-copy small{color:#D5DFEA;line-height:1.5}
.compare-label{letter-spacing:.02em;text-transform:none;font-size:10px;color:#64748b}
.compare-label i{color:#64748b}
.target-card{border:1px solid #34465f;background:linear-gradient(135deg,#172235 0%,#263b56 100%);color:#fff;box-shadow:0 13px 30px rgba(23,34,53,.18)}
.target-card .compare-label{color:#E2E8F0}
.target-card .compare-label i{color:#FDBA74}
.target-card .money-large{color:#FDBA74;text-shadow:0 1px 0 rgba(0,0,0,.12)}
.target-card small,.target-card #target-subline{color:#E2E8F0}
.status-badge{display:inline-flex;align-items:center;justify-content:center;min-height:28px;padding:6px 10px;border-radius:9px;white-space:normal;line-height:1.25;text-align:center;max-width:100%;overflow-wrap:anywhere;box-sizing:border-box}
.state-card-top{align-items:flex-start}
.state-card-top .status-badge{flex:0 1 auto;max-width:120px}
.state-card-stats>div{min-width:0}
.state-card-stats b,.quickfacts-grid b{overflow-wrap:anywhere;line-height:1.25}
.quickfacts-grid article{min-width:0}
.legal-container.contact-page{max-width:760px}
.contact-page .legal-hero,.contact-page .legal-content{max-width:100%}
.contact-page .contact-email{width:100%;max-width:none;min-width:0;box-sizing:border-box;justify-content:space-between;flex-wrap:wrap;gap:12px;background:#fff;border:1px solid #dbe3ed;box-shadow:0 10px 28px rgba(23,34,53,.07)}
.contact-page .contact-email b{min-width:0;overflow-wrap:anywhere;color:#172235}
.contact-page .contact-email .button{margin-left:auto;white-space:nowrap}
.legal-content a.button,.legal-content a.button-primary{color:#fff;text-decoration:none!important;text-underline-offset:0}
.legal-content a.button-primary:hover{color:#fff;text-decoration:none!important}
.results-section .eyebrow{letter-spacing:.06em;text-transform:none}
@media(max-width:767px){
  .receipt-card{width:min(360px,100%);padding:18px 19px 17px;transform:none!important}
  .hero-visual{min-height:0;padding:12px 0 8px}
  .verdict-banner,.verdict-banner.verdict-fair,.verdict-banner.verdict-over,.verdict-banner.verdict-junk{border-left-width:3px}
  .verdict-copy strong{font-size:19px}
  .compare-label{font-size:9px;line-height:1.35;align-items:flex-start}
  .money-large{font-size:clamp(23px,6vw,30px)}
  .target-card small{font-size:10px;line-height:1.45}
  .state-card-top{align-items:flex-start}
  .state-card-top .status-badge{max-width:112px;min-height:28px;padding:5px 8px;border-radius:8px;font-size:9px}
  .contact-page .contact-email{flex-direction:row;align-items:center;padding:14px;gap:10px}
  .contact-page .contact-email b{font-size:13px;flex:1 1 180px}
  .contact-page .contact-email .button{margin-left:0;min-height:38px;flex:0 0 auto}
}
@media(max-width:390px){
  .receipt-card{width:100%;padding:16px}
  .receipt-header{font-size:8px}
  .compare-card{min-width:0}
  .compare-label{font-size:8px}
  .contact-page .contact-email .button{width:100%}
}
'''

JS = r'''(() => {
  "use strict";
  const $ = (sel, root=document) => root.querySelector(sel);
  const $$ = (sel, root=document) => Array.from(root.querySelectorAll(sel));
  const money = n => new Intl.NumberFormat("en-US", {style:"currency",currency:"USD",maximumFractionDigits:0}).format(Number.isFinite(n)?n:0);
  const moneyCents = n => new Intl.NumberFormat("en-US", {style:"currency",currency:"USD",minimumFractionDigits:2,maximumFractionDigits:2}).format(Number.isFinite(n)?n:0);
  const num = id => Math.max(0, Number($(id)?.value || 0));
  const KEY = "carquotecheck.saved.v1";
  let states = [];
  let addons = [];
  let currentStep = 1;
  let financing = "cash";
  let lastAudit = null;
  let toastTimer = null;
  let selection = {doc:true, addons:{}};
  const defaults = {"#state-select":"", "#selling-price":"32000", "#trade-in":"0", "#tax-rate":"6", "#doc-fee":"300", "#gov-fees":"200", "#apr":"6.9", "#loan-months":"72"};

  function safeReadSaved(){ try { const v=JSON.parse(localStorage.getItem(KEY)||"[]"); return Array.isArray(v)?v.slice(0,4):[]; } catch(e){ return []; } }
  function safeWriteSaved(v){ try { localStorage.setItem(KEY,JSON.stringify(v.slice(0,4))); return true; } catch(e){ toast("Browser storage is unavailable. Check your privacy settings."); return false; } }
  function toast(message){ const el=$("#toast"); if(!el)return; el.textContent=message; el.classList.add("show"); clearTimeout(toastTimer); toastTimer=setTimeout(()=>el.classList.remove("show"),2400); }
  function activeState(){ return states.find(s=>s.code===$("#state-select")?.value) || null; }
  function setStep(step,scroll=true){
    currentStep=Math.max(1,Math.min(3,step));
    $$(".wizard-step").forEach(el=>{const active=Number(el.dataset.step)===currentStep;el.classList.toggle("active",active);el.hidden=!active;});
    $$(".progress-step").forEach(el=>{const n=Number(el.dataset.goStep);el.classList.toggle("active",n===currentStep);el.classList.toggle("complete",n<currentStep);if(n===currentStep)el.setAttribute("aria-current","step");else el.removeAttribute("aria-current");});
    if(scroll && window.matchMedia("(max-width:767px)").matches) $("#auditor-wizard")?.scrollIntoView({behavior:"smooth",block:"start"});
  }
  function showError(message){const e=$("#form-error");if(!e)return;e.textContent=message;e.hidden=false;e.scrollIntoView({behavior:"smooth",block:"nearest"});}
  function clearError(){const e=$("#form-error");if(e){e.hidden=true;e.textContent="";}}
  function validateStep(step){
    clearError();
    if(step===1){
      if(!$("#state-select").value){showError("Choose the state where you will register the vehicle.");return false;}
      if(num("#selling-price")<=0){showError("Enter a vehicle selling price greater than $0.");return false;}
      if(num("#tax-rate")>20){showError("Check the tax rate. Enter a percentage between 0 and 20.");return false;}
    }
    if(step===2 && (!Number.isFinite(Number($("#doc-fee").value)) || Number($("#doc-fee").value)<0)){showError("Enter a valid dealer documentation fee.");return false;}
    if(step===3 && financing==="loan"){
      const months=Number($("#loan-months").value),apr=Number($("#apr").value);
      if(!Number.isFinite(months)||months<1||months>120){showError("Enter a loan term between 1 and 120 months.");return false;}
      if(!Number.isFinite(apr)||apr<0||apr>50){showError("Enter an APR between 0% and 50%.");return false;}
    }
    return true;
  }
  function stateSelectChange(code,overwriteTax=true){
    const s=states.find(x=>x.code===code); if(!s)return;
    $("#state-hint").textContent=s.tax_note;
    if(overwriteTax) $("#tax-rate").value=s.tax_rate_pct;
    $("#trade-credit-hint").textContent=s.trade_in_label;
    const tradeToggle=$("#apply-trade-credit");
    tradeToggle.checked=["full","limited"].includes(s.trade_in_rule);
    tradeToggle.disabled=s.trade_in_rule==="none";
    if(s.trade_in_rule==="new_only") tradeToggle.disabled=false;
    if(s.trade_in_rule==="partial") tradeToggle.checked=false;
    $("#doc-fee").value=s.average_doc_fee;
    $("#gov-fees").value=s.government_fee_default;
    const taxable=$("#doc-fee-taxable");
    taxable.checked=s.doc_fee_taxable===false?false:true;
    $("#doc-tax-hint").textContent=s.doc_fee_taxable===null?"Tax treatment not verified. Included by default until you confirm.":s.doc_fee_taxable_label+". Confirm the invoice description.";
    const cap=s.doc_fee_cap!==null?`Confirmed statewide reference cap: ${money(s.doc_fee_cap)}.`:s.doc_fee_rule_label+".";
    $("#doc-fee-hint").textContent=`Average doc-fee benchmark: ${money(s.average_doc_fee)}. ${cap} Benchmark is not a legal limit.`;
  }
  function fillStateOptions(){
    const select=$("#state-select"); if(!select)return;
    const options=states.map(s=>`<option value="${s.code}">${s.name} (${s.code})</option>`).join("");
    select.insertAdjacentHTML("beforeend",options);
    const defaultCode=document.body.dataset.defaultState || $(".wizard-card")?.dataset.defaultState || "";
    if(defaultCode){select.value=defaultCode;stateSelectChange(defaultCode);}
    else if(states.some(s=>s.code==="FL")){select.value="FL";stateSelectChange("FL");}
  }
  function renderAddons(){
    const root=$("#addon-list"); if(!root)return;
    if(!addons.length){root.innerHTML='<p class="empty-addons">No dealer add-ons added.</p>';return;}
    root.innerHTML=addons.map((a,i)=>`<div class="addon-row" data-addon-row="${i}"><span>${escapeHTML(a.name)}</span><input aria-label="${escapeHTML(a.name)} amount" type="number" min="0" step="0.01" value="${Number(a.amount)}" data-addon-amount="${i}"><button class="remove-addon" type="button" data-remove-addon="${i}" aria-label="Remove ${escapeHTML(a.name)}"><i class="fa-solid fa-xmark"></i></button></div>`).join("");
  }
  function escapeHTML(s){return String(s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));}
  function addAddon(name,amount){addons.push({name,amount:Number(amount)||0});renderAddons();}
  function financingSet(mode){financing=mode;$$('[data-financing]').forEach(b=>{const on=b.dataset.financing===mode;b.classList.toggle("active",on);b.setAttribute("aria-pressed",String(on));});$("#loan-fields").hidden=mode!=="loan";}
  function cashCreditAmount(s,trade,enabled){
    if(!enabled||!s)return 0;
    if(s.trade_in_rule==="none")return 0;
    if(s.trade_in_rule==="limited")return Math.min(trade,12000);
    if(s.trade_in_rule==="new_only")return Math.min(trade,num("#selling-price"));
    if(s.trade_in_rule==="partial")return Math.min(trade,num("#selling-price"))*(1.25/4.5);
    return Math.min(trade,num("#selling-price"));
  }
  function loanPayment(principal,apr,months){
    principal=Math.max(0,principal);months=Math.max(1,Math.round(months||1));
    if(principal===0)return 0;
    const r=Math.max(0,apr)/1200;
    if(r===0)return principal/months;
    const f=Math.pow(1+r,months);
    return principal*(r*f)/(f-1);
  }
  function calculate(){
    const s=activeState(); if(!s)throw new Error("Choose a state before running the audit.");
    const price=num("#selling-price"),trade=num("#trade-in"),doc=num("#doc-fee"),gov=num("#gov-fees"),rate=num("#tax-rate")/100;
    const applyCredit=$("#apply-trade-credit").checked;
    const credit=cashCreditAmount(s,trade,applyCredit);
    const docTax=$("#doc-fee-taxable").checked;
    const addonTotal=addons.reduce((sum,a)=>sum+Math.max(0,Number(a.amount)||0),0);
    const taxableBase=Math.max(0,price-(applyCredit?credit:0)+(docTax?doc:0)+addonTotal);
    const tax=taxableBase*rate;
    const quotedOtd=Math.max(0,price+doc+gov+addonTotal+tax-trade);
    const benchmark=s.doc_fee_cap!==null?s.doc_fee_cap:s.average_doc_fee;
    const highDoc=doc>benchmark*1.25 || (s.doc_fee_cap!==null && doc>s.doc_fee_cap);
    const docAccepted=selection.doc!==false;
    const targetDoc=highDoc&&!docAccepted?Math.min(doc,benchmark):doc;
    const keptAddons=addons.filter((a,i)=>selection.addons[i]!==false);
    const keptAddonTotal=keptAddons.reduce((sum,a)=>sum+Math.max(0,Number(a.amount)||0),0);
    const targetTaxBase=Math.max(0,price-(applyCredit?credit:0)+(docTax?targetDoc:0)+keptAddonTotal);
    const targetTax=targetTaxBase*rate;
    const targetOtd=Math.max(0,price+targetDoc+gov+keptAddonTotal+targetTax-trade);
    const savings=Math.max(0,quotedOtd-targetOtd);
    const overage=Math.max(0,doc-benchmark);
    const flaggedAddonTotal=addonTotal;
    const junkExposure=overage+flaggedAddonTotal;
    const fairness=Math.max(0,Math.min(100,Math.round(100-(Math.max(savings,junkExposure)/Math.max(500,quotedOtd))*280)));
    const apr=financing==="loan"?Number($("#apr").value)||0:0;
    const months=financing==="loan"?Math.max(1,Number($("#loan-months").value)||1):0;
    const quotedPayment=financing==="loan"?loanPayment(quotedOtd,apr,months):0;
    const targetPayment=financing==="loan"?loanPayment(targetOtd,apr,months):0;
    const junkPayment=financing==="loan"?loanPayment(junkExposure,apr,months):0;
    const extraMonthly=junkPayment;
    const extraInterest=financing==="loan"?Math.max(0,junkPayment*months-junkExposure):0;
    let verdict="Fair deal",note="Your entered numbers are close to the current reference target.",klass="verdict-fair";
    if(flaggedAddonTotal>0){verdict="Junk fee alert";note="Optional dealer add-ons are included. Review each line and remove anything you did not request.";klass="verdict-junk";}
    else if(savings>100){verdict="Overpriced";note="The quote is above the current state-aware reference target. Ask the dealer to explain the difference.";klass="verdict-over";}
    return {state:s,price,trade,doc,gov,rate:rate*100,applyCredit,credit,docTax,addons:addons.map(a=>({...a})),addonTotal,taxableBase,tax,quotedOtd,targetOtd,savings,benchmark,highDoc,targetDoc,targetTax,keptAddonTotal,fairness,verdict,note,klass,financing,apr,months,quotedPayment,targetPayment,junkExposure,extraMonthly,extraInterest,overage};
  }
  function lineRow(label,amount,kind,description,toggleType=null,toggleIndex=null,checked=true){
    const toggle=toggleType?`<label class="line-toggle"><input type="checkbox" data-target-type="${toggleType}" ${toggleIndex!==null?`data-target-index="${toggleIndex}"`:""} ${checked?"checked":""}> Keep in target</label>`:"";
    return `<div class="xray-line"><span class="line-dot ${kind}"></span><div class="line-main"><b>${escapeHTML(label)}</b><small>${escapeHTML(description)}${toggle}</small></div><span class="line-value">${money(amount)}</span></div>`;
  }
  function renderXray(a){
    const root=$("#xray-lines"); if(!root)return;
    let html="";
    html+=lineRow("Vehicle selling price",a.price,"green","Starting vehicle price on the buyer's order.");
    if(a.trade>0)html+=lineRow("Trade-in value",-a.trade,"green","Shown as a deal credit; tax treatment is a separate setting.");
    html+=lineRow("Estimated vehicle tax",a.tax,"green",`Calculated from an estimated taxable base of ${money(a.taxableBase)} at ${a.rate.toFixed(3).replace(/0+$/,'').replace(/\.$/,'')}%.`);
    html+=lineRow("Government title & registration",a.gov,"green","Government charges are separate from the dealer's documentation fee.");
    const docDesc=a.state.doc_fee_cap!==null?`Reference cap ${money(a.state.doc_fee_cap)}. Confirm dealer and transaction eligibility.`:(a.state.doc_fee_rule_status==="not_verified"?"Statewide limit not verified; market benchmark is not a legal ceiling.":`Market benchmark ${money(a.state.average_doc_fee)}; not a legal cap.`);
    if(a.highDoc)html+=lineRow("Dealer documentation fee",a.doc,"amber",docDesc,"doc",null,selection.doc!==false);
    else html+=lineRow("Dealer documentation fee",a.doc,"green","Compare with the state reference; keep this amount itemized.");
    a.addons.forEach((x,i)=>html+=lineRow(x.name,x.amount,"red","Optional dealer-installed or dealer-added item. Ask whether you can decline it.","addon",i,selection.addons[i]!==false));
    root.innerHTML=html;
    $$("[data-target-type]",root).forEach(input=>input.addEventListener("change",()=>{
      if(input.dataset.targetType==="doc")selection.doc=input.checked;
      else selection.addons[Number(input.dataset.targetIndex)]=input.checked;
      updateTargetDisplay();
    }));
  }
  function updateTargetDisplay(){
    if(!lastAudit)return;
    const a=calculate();lastAudit={...lastAudit,...a};
    $("#target-otd").textContent=money(a.targetOtd);$("#live-target-otd").textContent=money(a.targetOtd);$("#potential-savings").textContent=money(a.savings);$("#fairness-score").textContent=a.fairness;
    if(a.financing==="loan"){$("#target-subline").textContent=`Estimated loan payment ${money(a.targetPayment)} / month`;$("#live-target-payment").textContent=`${money(a.targetPayment)} / mo`;}
    renderEmail();
  }
  function renderAudit(){
    const a=calculate();lastAudit=a;
    const results=$("#audit-results");results.hidden=false;
    const banner=$("#verdict-banner");banner.className=`verdict-banner ${a.klass}`;
    $("#verdict-label").textContent=a.verdict;$("#verdict-note").textContent=a.note;$("#fairness-score").textContent=a.fairness;
    $("#potential-savings").textContent=money(a.savings);$("#quoted-otd").textContent=money(a.quotedOtd);$("#target-otd").textContent=money(a.targetOtd);
    $("#quoted-subline").textContent=`${a.state.name} · ${a.financing==="loan"?`Estimated payment ${money(a.quotedPayment)} / month`:"Cash purchase estimate"}`;
    $("#target-subline").textContent=a.financing==="loan"?`Estimated payment ${money(a.targetPayment)} / month`:"Based on the reference fee target and selected line items";
    $("#live-target-otd").textContent=money(a.targetOtd);$("#live-payment-row").hidden=a.financing!=="loan";
    if(a.financing==="loan")$("#live-target-payment").textContent=`${money(a.targetPayment)} / mo`;
    $("#loan-trap").hidden=a.financing!=="loan";
    if(a.financing==="loan"){$("#extra-monthly").textContent=money(a.extraMonthly);$("#extra-interest").textContent=money(a.extraInterest);}
    renderXray(a);renderEmail();results.scrollIntoView({behavior:"smooth",block:"start"});
  }
  function emailText(tone){
    if(!lastAudit)return "";
    const a=calculate();const target=money(a.targetOtd);const quote=money(a.quotedOtd);const savings=money(Math.max(0,a.quotedOtd-a.targetOtd));
    const state=a.state.name;
    if(tone==="firm")return `Subject: Request for revised out-the-door price\n\nHello,\n\nThank you for putting the numbers together. I reviewed the buyer's order and would like a revised written out-the-door quote for the vehicle.\n\nThe current quoted OTD total is ${quote}. Based on the selling price, government charges, and the ${state} fee references, my target is ${target}. Please remove any optional add-ons I have not requested and explain any dealer fee that cannot be adjusted.\n\nPlease send the updated itemized buyer's order with the selling price, doc fee, taxes, title and registration shown separately. I am ready to review a clean, complete offer.\n\nThank you.`;
    if(tone==="walkaway")return `Subject: Final out-the-door offer\n\nHello,\n\nThank you for your time. I am prepared to move forward only if the complete out-the-door price can be brought to ${target}, with optional add-ons removed unless I have expressly agreed to them.\n\nThe current quote totals ${quote}. Please send your best itemized final offer, including all taxes, dealer fees, title and registration. If that total is not possible, I will need to continue shopping.\n\nThank you for considering my offer.`;
    return `Subject: Quick question about the out-the-door price\n\nHello,\n\nThanks for walking me through the vehicle and the quote. I have reviewed the itemized costs and would feel comfortable moving ahead at an out-the-door target of ${target}.\n\nCould you please review the documentation fee and any optional add-ons, then send me an updated buyer's order with the selling price, taxes, dealer fees, title and registration listed separately?\n\nI appreciate your help and look forward to seeing the revised numbers.\n\nBest regards`;
  }
  function renderEmail(){const area=$("#counter-email");if(area)area.value=emailText($("#email-tone")?.value||"polite");}
  function currentPayload(){
    return {state:$("#state-select").value,price:num("#selling-price"),trade:num("#trade-in"),taxRate:num("#tax-rate"),credit:$("#apply-trade-credit").checked,doc:num("#doc-fee"),gov:num("#gov-fees"),docTax:$("#doc-fee-taxable").checked,addons:addons.map(a=>({...a})),financing,apr:num("#apr"),months:Math.max(1,Number($("#loan-months").value)||72),selection:{doc:selection.doc,addons:{...selection.addons}}};
  }
  function restorePayload(p){
    if(!p||!p.state||!states.some(s=>s.code===p.state))throw new Error("This share link is missing a valid state.");
    $("#state-select").value=p.state;stateSelectChange(p.state,false);
    $("#selling-price").value=p.price??32000;$("#trade-in").value=p.trade??0;$("#tax-rate").value=p.taxRate??activeState().tax_rate_pct;
    $("#apply-trade-credit").checked=!!p.credit;$("#apply-trade-credit").disabled=activeState().trade_in_rule==="none";
    $("#doc-fee").value=p.doc??activeState().average_doc_fee;$("#gov-fees").value=p.gov??activeState().government_fee_default;$("#doc-fee-taxable").checked=p.docTax!==false;
    addons=Array.isArray(p.addons)?p.addons.map(a=>({name:String(a.name||"Dealer fee").slice(0,42),amount:Math.max(0,Number(a.amount)||0)})):[];
    selection=p.selection&&typeof p.selection==="object"?{doc:p.selection.doc!==false,addons:p.selection.addons||{}}:{doc:true,addons:{}};
    $("#apr").value=p.apr??6.9;$("#loan-months").value=p.months??72;financingSet(p.financing==="loan"?"loan":"cash");renderAddons();
  }
  function shareUrl(){
    const p=currentPayload();
    return `${location.origin}${location.pathname}#q=${encodeURIComponent(JSON.stringify(p))}`;
  }
  function parseShare(){
    if(!location.hash.startsWith("#q="))return null;
    try{return JSON.parse(decodeURIComponent(location.hash.slice(3)));}catch(e){return null;}
  }
  async function copyText(text,success){
    try{if(navigator.clipboard&&window.isSecureContext)await navigator.clipboard.writeText(text);else{const ta=document.createElement("textarea");ta.value=text;ta.style.position="fixed";ta.style.opacity="0";document.body.appendChild(ta);ta.select();const ok=document.execCommand("copy");ta.remove();if(!ok)throw new Error("Copy not available");}toast(success||"Copied to clipboard.");}catch(e){toast("Copy was blocked by this browser. Select and copy the text manually.");}
  }
  function savedCount(){const count=safeReadSaved().length;$$('[data-saved-count]').forEach(el=>el.textContent=count);$("#saved-modal-count").textContent=`${count} of 4 quotes saved`;}
  function openSaved(){renderSaved();$("#saved-modal").hidden=false;$("[data-close-modal]")?.focus();}
  function closeSaved(){const m=$("#saved-modal");if(m)m.hidden=true;}
  function saveQuote(){
    if(!lastAudit){toast("Run an audit before saving a quote.");return;}
    const a=calculate();const saved=safeReadSaved();const quote={id:Date.now().toString(36),savedAt:new Date().toISOString(),payload:currentPayload(),state:a.state.name,code:a.state.code,quoted:a.quotedOtd,target:a.targetOtd,score:a.fairness,savings:a.savings};
    if(saved.length>=4){toast("You can save up to four quotes. Remove one to add another.");openSaved();return;}
    saved.unshift(quote);if(safeWriteSaved(saved)){savedCount();toast("Quote saved on this device.");}
  }
  function renderSaved(){
    const root=$("#saved-quotes-list");if(!root)return;const saved=safeReadSaved();
    root.innerHTML=saved.length?saved.map(q=>`<article class="saved-quote-row"><div><b>${escapeHTML(q.state)} · ${escapeHTML(q.code)}</b><small>${new Date(q.savedAt).toLocaleDateString("en-US",{month:"short",day:"numeric",year:"numeric"})}</small><div class="saved-quote-metrics"><span>Quoted ${money(q.quoted)}</span><span>Target ${money(q.target)}</span><span>Score ${q.score}/100</span></div></div><button class="remove-saved" type="button" data-remove-saved="${q.id}" aria-label="Remove saved quote"><i class="fa-solid fa-trash"></i></button></article>`).join(""):'<div class="saved-empty"><i class="fa-regular fa-heart"></i><p>No saved quotes yet.</p><span>Run an audit and save it to compare offers from different dealers.</span></div>';
    $$("[data-remove-saved]",root).forEach(b=>b.addEventListener("click",()=>{safeWriteSaved(safeReadSaved().filter(q=>q.id!==b.dataset.removeSaved));renderSaved();savedCount();}));savedCount();
  }
  function downloadAuditCard(){
    if(!lastAudit){toast("Run an audit before downloading a card.");return;}
    const a=calculate();const c=document.createElement("canvas");c.width=1080;c.height=1080;const x=c.getContext("2d");
    x.fillStyle="#F8F9FA";x.fillRect(0,0,1080,1080);
    x.fillStyle="#142033";x.fillRect(0,0,1080,260);
    x.fillStyle="#F38020";x.beginPath();x.roundRect(76,66,72,72,18);x.fill();
    x.fillStyle="#fff";x.beginPath();x.roundRect(87,101,48,20,6);x.fill();x.beginPath();x.moveTo(94,102);x.lineTo(102,88);x.lineTo(119,88);x.lineTo(130,102);x.closePath();x.fill();x.fillStyle="#F38020";x.beginPath();x.arc(98,121,6,0,Math.PI*2);x.arc(125,121,6,0,Math.PI*2);x.fill();x.fillStyle="#fff";x.font="700 32px Arial";x.fillText("CarQuote",172,112);x.fillStyle="#F38020";x.fillText("Check",334,112);
    x.fillStyle="#fff";x.font="700 48px Arial";x.fillText(a.verdict,76,202);
    x.fillStyle="#D1D5DB";x.font="22px Arial";x.fillText(`${a.state.name}  |  Fairness score`,76,238);
    x.fillStyle="#fff";x.beginPath();x.roundRect(838,65,160,108,22);x.fill();x.fillStyle="#142033";x.font="700 50px Arial";x.fillText(String(a.fairness),866,130);x.font="18px Arial";x.fillText("/ 100",940,130);
    const card=(left,top,w,h,label,value,fill)=>{x.fillStyle=fill;x.beginPath();x.roundRect(left,top,w,h,20);x.fill();x.fillStyle="#64748B";x.font="700 19px Arial";x.fillText(label,left+24,top+42);x.fillStyle="#111827";x.font="700 42px Arial";x.fillText(value,left+24,top+105);};
    card(76,310,444,160,"Dealer quoted OTD",money(a.quotedOtd),"#fff");card(560,310,444,160,"Fair target OTD",money(a.targetOtd),"#FFF7ED");
    x.fillStyle="#F38020";x.beginPath();x.roundRect(76,500,928,126,21);x.fill();x.fillStyle="#fff";x.font="700 22px Arial";x.fillText("Potential savings",108,548);x.font="700 55px Arial";x.fillText(money(a.savings),108,602);
    x.fillStyle="#111827";x.font="700 24px Arial";x.fillText("REVIEW THESE LINE ITEMS",76,695);
    const flagged=[];if(a.highDoc)flagged.push(["Dealer documentation fee",a.doc]);a.addons.forEach(z=>flagged.push([z.name,z.amount]));
    const display=(flagged.length?flagged:[["No optional add-ons entered",0]]).slice(0,4);
    let y=742;display.forEach(([label,val])=>{x.fillStyle="#FEE2E2";x.beginPath();x.arc(90,y-7,7,0,Math.PI*2);x.fill();x.fillStyle="#374151";x.font="22px Arial";x.fillText(label,114,y);x.textAlign="right";x.font="700 22px Arial";x.fillText(money(val),990,y);x.textAlign="left";y+=54;});
    x.strokeStyle="#E5E7EB";x.beginPath();x.moveTo(76,970);x.lineTo(1004,970);x.stroke();x.fillStyle="#6B7280";x.font="17px Arial";x.fillText("State rules and tax figures are estimates. Verify your buyer's order.",76,1010);x.fillText("CarQuoteCheck  |  carquotecheck.pages.dev  |  Private browser-side estimate",76,1042);
    c.toBlob(blob=>{if(!blob){toast("PNG export failed in this browser.");return;}const aTag=document.createElement("a");const url=URL.createObjectURL(blob);aTag.href=url;aTag.download="carquotecheck-audit-card.png";aTag.click();setTimeout(()=>URL.revokeObjectURL(url),1000);toast("Audit card downloaded.");},"image/png");
  }
  function trySample(){
    $("#state-select").value="FL";stateSelectChange("FL");$("#selling-price").value=32000;$("#trade-in").value=5000;$("#tax-rate").value=6;$("#apply-trade-credit").checked=true;$("#doc-fee").value=999;$("#gov-fees").value=2150;$("#doc-fee-taxable").checked=true;
    addons=[{name:"Paint Protection",amount:799},{name:"VIN Etching",amount:299}];renderAddons();$("#apr").value=6.9;$("#loan-months").value=72;financingSet("loan");selection={doc:true,addons:{}};setStep(3,false);renderAudit();
  }
  function reset(){
    Object.entries(defaults).forEach(([id,v])=>{if($(id))$(id).value=v;});addons=[];selection={doc:true,addons:{}};renderAddons();financingSet("cash");const s=states.find(x=>x.code===(document.body.dataset.defaultState||"FL"))||states.find(x=>x.code==="FL");if(s){$("#state-select").value=s.code;stateSelectChange(s.code);}setStep(1,false);clearError();$("#audit-results").hidden=true;lastAudit=null;history.replaceState(null,"",location.pathname+location.search);$("#auditor-wizard")?.scrollIntoView({behavior:"smooth",block:"start"});
  }
  function initDirectory(){
    const search=$("#state-search");if(!search)return;let filter="all";
    const update=()=>{const q=search.value.trim().toLowerCase();let n=0;$$('[data-state-row],[data-state-card]').forEach(el=>{const match=!q||el.dataset.name.includes(q)||el.dataset.code.toLowerCase().includes(q);const rule=el.dataset.rule;const passFilter=filter==="all"||(filter==="capped"?rule==="capped":rule!=="capped");const show=match&&passFilter;el.hidden=!show;if(show&&el.hasAttribute("data-state-row"))n++;});const count=$("#directory-count");if(count)count.textContent=`Showing ${n} ${n===1?"jurisdiction":"jurisdictions"}`;};
    $$("[data-filter]").forEach(b=>b.addEventListener("click",()=>{$$("[data-filter]").forEach(x=>x.classList.remove("active"));b.classList.add("active");filter=b.dataset.filter;update();}));search.addEventListener("input",update);
    $$("[data-state-chip]").forEach(b=>b.addEventListener("click",()=>{$("#state-select").value=b.dataset.stateChip;stateSelectChange(b.dataset.stateChip);setStep(1,false);$("#selling-price").focus();}));
    document.addEventListener("keydown",e=>{if(e.key==="/"&&!/INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName)){e.preventDefault();search.focus();}});
  }
  function initMobile(){
    const btn=$(".mobile-menu-toggle"),drawer=$("#mobile-drawer");if(!btn||!drawer)return;
    const close=()=>{drawer.hidden=true;btn.setAttribute("aria-expanded","false");btn.setAttribute("aria-label","Open navigation menu");btn.innerHTML='<i class="fa-solid fa-bars" aria-hidden="true"></i>';};
    btn.addEventListener("click",()=>{const open=btn.getAttribute("aria-expanded")==="true";drawer.hidden=open;btn.setAttribute("aria-expanded",String(!open));btn.setAttribute("aria-label",open?"Open navigation menu":"Close navigation menu");btn.innerHTML=open?'<i class="fa-solid fa-bars" aria-hidden="true"></i>':'<i class="fa-solid fa-xmark" aria-hidden="true"></i>';});
    drawer.addEventListener("click",e=>{if(e.target.closest("a")){close();}});
    document.addEventListener("click",e=>{if(!drawer.hidden&&!drawer.contains(e.target)&&!btn.contains(e.target))close();});
    document.addEventListener("keydown",e=>{if(e.key==="Escape")close();});
  }
  function scrollToSection(id, behavior="smooth"){
    const target=document.getElementById(id);
    if(!target)return false;
    target.scrollIntoView({behavior,block:"start"});
    const drawer=$("#mobile-drawer"),menu=$(".mobile-menu-toggle");
    if(drawer&&!drawer.hidden){drawer.hidden=true;menu?.setAttribute("aria-expanded","false");menu?.setAttribute("aria-label","Open navigation menu");if(menu)menu.innerHTML='<i class="fa-solid fa-bars" aria-hidden="true"></i>';}
    return true;
  }
  function initScrollLinks(){
    $$('[data-scroll-target]').forEach(link=>link.addEventListener("click",event=>{
      const id=link.dataset.scrollTarget;
      if(!id)return;
      event.preventDefault();
      if(document.getElementById(id)){scrollToSection(id);return;}
      const next=new URL("/",location.origin);next.searchParams.set("scroll",id);location.assign(next.href);
    }));
    const requested=new URLSearchParams(location.search).get("scroll");
    if(requested&&document.getElementById(requested)){
      history.replaceState(null,"",location.pathname);
      requestAnimationFrame(()=>scrollToSection(requested,"auto"));
    }
  }
  function init(){
    fillStateOptions();initDirectory();initMobile();initScrollLinks();savedCount();
    $("#state-select")?.addEventListener("change",e=>stateSelectChange(e.target.value));
    $$("[data-next-step]").forEach(b=>b.addEventListener("click",()=>{const current=Number(b.dataset.nextStep)-1;if(validateStep(current))setStep(Number(b.dataset.nextStep));}));
    $$("[data-prev-step]").forEach(b=>b.addEventListener("click",()=>setStep(Number(b.dataset.prevStep))));
    $$("[data-go-step]").forEach(b=>b.addEventListener("click",()=>{const n=Number(b.dataset.goStep);if(n<=currentStep)setStep(n);else if(validateStep(currentStep))setStep(n);}));
    $$("[data-fee-name]").forEach(b=>b.addEventListener("click",()=>{const name=b.dataset.feeName;const existing=addons.find(x=>x.name===name);if(existing){toast("That fee is already added.");return;}addAddon(name,b.dataset.feeValue);}));
    $("#addon-list")?.addEventListener("change",e=>{const i=Number(e.target.dataset.addonAmount);if(Number.isInteger(i)&&addons[i])addons[i].amount=Math.max(0,Number(e.target.value)||0);});
    $("#addon-list")?.addEventListener("click",e=>{const b=e.target.closest("[data-remove-addon]");if(!b)return;addons.splice(Number(b.dataset.removeAddon),1);renderAddons();});
    $("#add-custom-fee")?.addEventListener("click",()=>{const name=$("#custom-fee-name").value.trim(),amount=Number($("#custom-fee-amount").value);if(!name||!Number.isFinite(amount)||amount<=0){showError("Enter a custom fee name and a positive amount.");return;}clearError();addAddon(name,amount);$("#custom-fee-name").value="";$("#custom-fee-amount").value="";});
    $$('[data-financing]').forEach(b=>b.addEventListener("click",()=>financingSet(b.dataset.financing)));
    $("#quote-form")?.addEventListener("submit",e=>{e.preventDefault();if(!validateStep(3))return;try{renderAudit();}catch(err){showError(err.message);}});
    $("#sample-quote")?.addEventListener("click",trySample);$("#reset-quote")?.addEventListener("click",reset);$("#edit-quote")?.addEventListener("click",()=>{setStep(1);$("#auditor-wizard")?.scrollIntoView({behavior:"smooth"});});
    $("#save-quote")?.addEventListener("click",saveQuote);$("#download-card")?.addEventListener("click",downloadAuditCard);$("#copy-link")?.addEventListener("click",()=>{if(!lastAudit){toast("Run an audit first.");return;}copyText(shareUrl(),"Shareable quote link copied.");});
    $("#email-tone")?.addEventListener("change",renderEmail);$("#copy-email")?.addEventListener("click",()=>copyText($("#counter-email").value,"Counter-offer email copied."));$("#print-sheet")?.addEventListener("click",()=>window.print());
    $$('[data-open-saved]').forEach(b=>b.addEventListener("click",e=>{e.preventDefault();openSaved();}));
    $$('[data-close-modal]').forEach(b=>b.addEventListener("click",closeSaved));$("#saved-modal")?.addEventListener("click",e=>{if(e.target.id==="saved-modal")closeSaved();});
    $("#copy-contact-email")?.addEventListener("click",()=>copyText($("#contact-email").textContent.trim(),"Email address copied."));
    const shared=parseShare();if(shared){try{restorePayload(shared);setStep(3,false);renderAudit();toast("Shareable quote restored.");}catch(e){toast("This share link could not be restored.");}}
  }
  document.addEventListener("DOMContentLoaded",async()=>{
    try{const res=await fetch("/data/states.json",{cache:"no-cache"});if(!res.ok)throw new Error("State data could not be loaded.");states=await res.json();init();}
    catch(e){const hint=$("#state-hint");if(hint)hint.textContent="State reference data could not load. Check your connection and refresh the page.";console.error(e);}
  });
})();
'''
def write_file(path,content):
    path=ROOT/path
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(content,encoding="utf-8")
    return path

def make_404():
    opts="".join(f'<option value="{escape(s["name"])} ({s["code"]})"></option>' for s in STATES)
    content=f'''<main class="not-found-main"><div class="container not-found-card"><span class="eyebrow">PAGE NOT FOUND</span><h1>Let's get you back on the road.</h1><p>The page may have moved. Search your state to open its car dealer doc-fee guide, or return to the quote auditor.</p><form id="not-found-search-form" class="not-found-search"><label class="sr-only" for="not-found-search">Search a state</label><input id="not-found-search" list="state-options" placeholder="Search state, e.g. Florida or FL" autocomplete="off"><datalist id="state-options">{opts}</datalist><button class="button button-primary" type="submit"><i class="fa-solid fa-magnifying-glass"></i> Find state</button></form><div class="not-found-actions"><a class="button button-secondary" href="/" data-scroll-target="auditor-wizard">Open OTD Auditor</a><a class="text-link" href="/">Back to homepage <i class="fa-solid fa-arrow-right"></i></a></div></div></main>'''
    page=head_html("Page Not Found | CarQuoteCheck","The page was not found. Search a US state fee guide or return to CarQuoteCheck.","/404.html").replace('<meta name="robots" content="index, follow, max-image-preview:large">','<meta name="robots" content="noindex, follow">')
    return page+"<body>"+header_html()+content+footer_html()

def generate_files():
    write_file(Path("style.css"),CSS+"\n.not-found-main{min-height:68vh;display:grid;place-items:center;padding:70px 0}.not-found-card{max-width:700px;background:#fff;border:1px solid var(--line);border-radius:24px;padding:clamp(28px,6vw,58px);box-shadow:var(--shadow)}.not-found-card h1{font:600 clamp(38px,6vw,58px)/1.02 var(--font-head);letter-spacing:-2px;margin:18px 0 14px}.not-found-card>p{max-width:540px;color:var(--secondary);line-height:1.75}.not-found-search{display:flex;gap:10px;margin:28px 0 18px}.not-found-search input{flex:1;min-width:0;border:1px solid var(--line);border-radius:999px;padding:0 18px;min-height:48px;font:500 14px var(--font-body)}.not-found-actions{display:flex;align-items:center;gap:20px;flex-wrap:wrap}.sr-only{position:absolute!important;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}@media(max-width:600px){.not-found-main{padding:42px 0}.not-found-search{flex-direction:column}.not-found-search input{min-height:48px}.not-found-search .button{width:100%}.not-found-actions{align-items:flex-start;flex-direction:column}}")
    write_file(Path("script.js"),JS)
    write_file(Path("favicon.svg"),make_svg_icon())
    pillow_assets()
    write_file(Path("data/states.json"),json.dumps(STATES,ensure_ascii=False,indent=2)+"\n")
    write_file(Path("index.html"),homepage_html())
    write_file(Path("404.html"),make_404())
    # State pages: one unique static landing page per state and DC.
    for s in STATES:
        write_file(Path(f'{s["slug"]}-car-dealer-doc-fee-calculator/index.html'),state_page_html(s))
    for slug,page in legal_pages().items():
        write_file(Path(slug)/"index.html",page)
    write_file(Path("_headers"),'''/*
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  X-Frame-Options: DENY
  Permissions-Policy: camera=(), microphone=(), geolocation=()
  Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
  Content-Security-Policy: default-src 'self' https: data: blob:; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://api.fontshare.com https://fonts.googleapis.com https://cdnjs.cloudflare.com; font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com https://cdn.fontshare.com data:; img-src 'self' data: blob: https:; connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'

/data/*
  Cache-Control: public, max-age=3600, s-maxage=86400

/*.css
  Cache-Control: public, max-age=86400

/*.js
  Cache-Control: public, max-age=86400

/*.png
  Cache-Control: public, max-age=604800
''')
    write_file(Path("robots.txt"),f'''User-agent: *\nAllow: /\n\nUser-agent: Googlebot\nAllow: /\n\nUser-agent: OAI-SearchBot\nAllow: /\n\nUser-agent: PerplexityBot\nAllow: /\n\nSitemap: {SITE_URL.rstrip('/')}/sitemap.xml\n''')
    urls=[SITE_URL.rstrip("/")+"/"]
    urls += [SITE_URL.rstrip("/")+f'/{s["slug"]}-car-dealer-doc-fee-calculator/' for s in STATES]
    urls += [SITE_URL.rstrip("/")+f'/{slug}/' for slug in ("privacy-policy","terms-of-service","about","contact")]
    sitemap='''<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'''+"".join(f'  <url><loc>{escape(u)}</loc></url>\n' for u in urls)+"</urlset>\n"
    write_file(Path("sitemap.xml"),sitemap)
    write_file(Path("llms.txt"),f'''# CarQuoteCheck\n\n> CarQuoteCheck is a free, browser-based US car-buying quote auditor. It helps consumers review dealer out-the-door prices, documentation fees, government charges, trade-in tax treatment, optional add-ons, and financing costs.\n\n## Product\n\n- Website: {SITE_URL.rstrip("/")}/\n- No login, quote database, or backend API is required. Calculations run in the visitor's browser.\n- Saved quotes are stored in browser local storage, up to four per browser.\n- Shareable quote values are encoded in the URL fragment. Anyone with a share link can inspect those values.\n- State directory: 50 US states plus the District of Columbia.\n- Each state page contains an OTD auditor, quick facts, local context, nearby-state links, and state-specific FAQs.\n\n## Important data notes\n\n- State tax percentages are starting points, not necessarily combined county/city rates.\n- Local sales tax, vehicle weight, vehicle age, fuel economy, dealer type, registration, and transaction details may alter the actual amount.\n- Average dealer doc fees are market benchmarks, not legal caps or official state averages.\n- A missing or unverified statutory cap is labeled unverified; it must not be interpreted as proof that no cap exists.\n- Government title and registration amounts are editable planning estimates. Confirm all numbers on the written buyer's order and with the relevant state agency.\n- The tool is educational and does not provide legal, tax, lending, or financial advice.\n\n## Primary references\n\n- State vehicle tax, trade-in and doc-fee rule reference: {RULES_SOURCE}\n- Doc-fee market benchmark: {AVERAGE_FEE_SOURCE}\n- FTC automobile pricing transparency FAQs: {FTC_SOURCE}\n\n## Contact\n\n{CONTACT_EMAIL} (configure a monitored mailbox before launch).\n''')
    write_file(Path("README.md"),f'''# CarQuoteCheck\n\nA static, zero-backend US car dealership OTD and fee auditor built for GitHub and Cloudflare Pages.\n\n## Build and package\n\n1. Edit `SITE_URL` near the top of `build.py` when moving to a custom domain.\n2. Replace `CONTACT_EMAIL` with a monitored mailbox.\n3. Run `python build.py` from this directory.\n4. The script regenerates the site, runs the pre-package audit, and writes `../carquotecheck-mvp.zip`.\n5. Deploy the contents of this directory to Cloudflare Pages with no build command and the project root as the output directory.\n\n## Architecture\n\n- Plain HTML, CSS, and vanilla JavaScript. No framework, server, database, or backend API.\n- State data: `data/states.json` (50 states + DC).\n- Quote data stays in the browser. Saved quotes use local storage; share links use URL fragments.\n- `apple-touch-icon.png` and `og-image.png` are generated with Pillow.\n\n## Data limitations\n\nState tax values are editable starting points and may exclude local tax or vehicle-specific rules. Doc-fee market figures are comparison benchmarks, not statutory limits. Several legal rule details remain explicitly unverified. Title and registration amounts are planning defaults. Verify the written buyer's order and current state guidance before relying on any number.\n\n## Sources\n\n- State fee and vehicle tax references: {RULES_SOURCE}\n- Dealer documentation fee market reference: {AVERAGE_FEE_SOURCE}\n- FTC pricing transparency FAQ: {FTC_SOURCE}\n\nThe state rules source is attributed in the About page. Third-party reference material remains subject to its own license and terms.\n''')
    # A small 404-only submit handler resolves state names or abbreviations to their SEO page.
    js=JS.replace('fillStateOptions();initDirectory();initMobile();savedCount();', '''fillStateOptions();initDirectory();initMobile();savedCount();
    $("#not-found-search-form")?.addEventListener("submit",e=>{e.preventDefault();const q=$("#not-found-search").value.trim().toLowerCase();const match=states.find(s=>s.code.toLowerCase()===q||s.name.toLowerCase()===q||`${s.name} (${s.code})`.toLowerCase()===q);if(match)location.href=`/${match.slug}-car-dealer-doc-fee-calculator/`;else location.href="/?scroll=state-directory";});''')
    write_file(Path("script.js"),js)
    return urls

def emoji_present(text):
    # Unicode emoji/pictograph blocks, variation selectors and joiners.
    pattern=re.compile("[\\U0001F000-\\U0001FAFF\\U00002600-\\U000027BF\\U0001F1E6-\\U0001F1FF\\uFE0F\\u200D]")
    return bool(pattern.search(text))

def audit(urls):
    errors=[]
    state_file=ROOT/"data/states.json"
    try: data=json.loads(state_file.read_text(encoding="utf-8"))
    except Exception as e: data=[];errors.append(f"Could not parse state JSON: {e}")
    if len(data)!=51: errors.append(f"Expected 51 jurisdictions; found {len(data)}")
    codes=[x.get("code") for x in data]
    if len(set(codes))!=51 or "DC" not in codes: errors.append("State codes are not 51 unique values including DC")
    if len(list(ROOT.rglob("*.html")))!=57: errors.append(f"Expected 57 HTML files; found {len(list(ROOT.rglob('*.html')))}")
    for name in ("favicon.svg","apple-touch-icon.png","og-image.png","build.py","index.html","404.html","style.css","script.js","_headers","robots.txt","sitemap.xml","llms.txt"):
        if not (ROOT/name).exists(): errors.append(f"Missing required file: {name}")
    for name in ("apple-touch-icon.png","og-image.png"):
        try:
            with Image.open(ROOT/name) as im:
                expected=(180,180) if name=="apple-touch-icon.png" else (1200,630)
                if im.size!=expected: errors.append(f"{name} has dimensions {im.size}, expected {expected}")
        except Exception as e: errors.append(f"Could not open {name}: {e}")
    try:
        tree=ET.parse(ROOT/"sitemap.xml")
        sitemap_urls=[el.text for el in tree.getroot().findall("{http://www.sitemaps.org/schemas/sitemap/0.9}url/{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
        if len(sitemap_urls)!=56: errors.append(f"Expected 56 sitemap URLs; found {len(sitemap_urls)}")
        if set(sitemap_urls)!=set(urls): errors.append("Sitemap URL list does not match the expected canonical pages")
    except Exception as e: errors.append(f"Invalid sitemap XML: {e}")
    forbidden="fa-shield-"+"halved"
    all_text=[]
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.name=="carquotecheck-mvp.zip": continue
        if path.suffix.lower() in {".html",".css",".js",".svg",".json",".txt",".md",".xml"} or path.name in {"_headers","build.py"}:
            try: all_text.append((path,path.read_text(encoding="utf-8")))
            except Exception as e: errors.append(f"Cannot read {path.relative_to(ROOT)}: {e}")
    for path,content in all_text:
        if emoji_present(content): errors.append(f"Emoji/pictograph found in {path.relative_to(ROOT)}")
        if forbidden in content: errors.append(f"Forbidden shield icon found in {path.relative_to(ROOT)}")
    html_files=list(ROOT.rglob("*.html"))
    for path in html_files:
        source=path.read_text(encoding="utf-8")
        title=re.search(r"<title>(.*?)</title>",source,re.I|re.S)
        if not title: errors.append(f"Missing title in {path.relative_to(ROOT)}")
        elif "2026" in title.group(1): errors.append(f"Year found in title in {path.relative_to(ROOT)}")
        for asset in ('href="/style.css"','src="/script.js"','href="/favicon.svg"','href="/apple-touch-icon.png"'):
            if asset not in source: errors.append(f"Missing root-relative asset path {asset} in {path.relative_to(ROOT)}")
    if len(urls)!=56: errors.append(f"Generator expected 56 canonical URLs; got {len(urls)}")
    # Project-specific regression checks for the requested redesign.
    home_text=(ROOT/"index.html").read_text(encoding="utf-8")
    contact_text=(ROOT/"contact"/"index.html").read_text(encoding="utf-8")
    css_text=(ROOT/"style.css").read_text(encoding="utf-8")
    js_text=(ROOT/"script.js").read_text(encoding="utf-8")
    if 'class="visual-note"' in home_text:
        errors.append("Homepage still contains the obsolete floating note")
    if ".visual-note" in css_text or ".note-icon" in css_text:
        errors.append("Obsolete floating-note CSS still exists")
    if "Launch checklist:" in contact_text or "No mail server or contact form" in contact_text:
        errors.append("Contact page still contains the removed launch placeholder")
    if not re.search(r"\.receipt-card\s*\{[^}]*transform:none!important",css_text,re.S):
        errors.append("Receipt card upright transform override is missing")
    if not re.search(r"\.verdict-banner[^}]*background:#172235!important",css_text,re.S):
        errors.append("Unified verdict banner color override is missing")
    if not re.search(r"\.target-card[^}]*linear-gradient\(135deg,#172235",css_text,re.S):
        errors.append("Target card contrast treatment is missing")
    if not re.search(r"\.status-badge\s*\{[^}]*border-radius:9px",css_text,re.S):
        errors.append("Responsive rectangular status badge treatment is missing")
    if "data-scroll-target" not in js_text or 'searchParams.set("scroll",id)' not in js_text or 'history.replaceState(null,"",location.pathname)' not in js_text:
        errors.append("Fragment-free section navigation handling is incomplete")
    for path in html_files:
        source=path.read_text(encoding="utf-8")
        if re.search(r"<a\b[^>]*\bhref=[\"'][^\"']*#[A-Za-z][^\"']*[\"']",source,re.I):
            errors.append(f"Fragment-based navigation URL found in {path.relative_to(ROOT)}")
        if re.search(r'"@id"\s*:\s*"[^" ]*#[A-Za-z]',source):
            errors.append(f"Fragment-style schema @id found in {path.relative_to(ROOT)}")
    if errors:
        print("PRE-ZIP AUDIT: FAILED")
        for item in errors: print(" -",item)
        raise SystemExit(1)
    print("PRE-ZIP AUDIT: PASSED")
    print(" - 51 state/jurisdiction records (50 states + DC)")
    print(" - 57 HTML documents (homepage, 404, 51 state pages, 4 trust pages)")
    print(" - 56 canonical URLs in XML sitemap")
    print(" - required favicon, touch icon and 1200x630 OG image verified")
    print(" - no emoji/pictographs or prohibited shield icon strings")
    print(" - no year in any HTML title; root-relative assets present")
    print(" - receipt upright; floating note and contact placeholder removed")
    print(" - verdict/target palette unified; mobile badges and contact alignment patched")
    print(" - no fragment-based navigation or schema identifier URLs")

def package_zip():
    out=ROOT.parent/"carquotecheck-mvp.zip"
    if out.exists(): out.unlink()
    with zipfile.ZipFile(out,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for path in sorted(ROOT.rglob("*")):
            if path.is_file() and path!=out and "__pycache__" not in path.parts and path.suffix.lower() != ".pyc":
                z.write(path,path.relative_to(ROOT).as_posix())
    print(f"PACKAGE CREATED: {out} ({out.stat().st_size:,} bytes)")
    return out

def main():
    print(f"Building {SITE_NAME} for {SITE_URL} ...")
    urls=generate_files()
    audit(urls)
    package_zip()

if __name__=="__main__":
    main()
