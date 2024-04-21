# WebScraper pro stránku bazos.cz
Jedná se o úkol zpracovaný pro stáž v Siemensu. <br>
Toto bylo zadáním: <br>
Z webové adresy: [bazoš](https://www.bazos.cz/) vyscrapujte údaje o prodeji koní. Atributy, které jsou pro zájemce o koupi koně důležité jsou: cena, kontaktní osoba, telefon, lokalita, datum vytvoření inzerátu, věk koně, barva, plemeno, výška kohoutku (KVH). Údaje uložte do souboru typu .csv. Poté připravte automatické odesílání dat pomocí 
e-mailu. Script by měl být konfigurovatelný prostřednictvím jednoduchého config souboru (e-mailové adresy, předmět e-mailu, text e-mailu, frekvence spouštění scriptu a čas odesílání e-mailu). 

## Popis kódu
### Funkce scraper(driver,url,max_pages)
Nejprve jsem si nadefinoval funkci, která bere 3 argumenty: driver, čímž specifikuji jaký driver z knihovny selenium použiji(firefox,Chrome), zde by stálo za to zdůraznit, že můj kód byl celou dobu stavěn na driveru Firefox a pro ten je také optimalizovaný. Dále url, kde specifikuji url stránky a max_pages, čímž si nastavím kolik stránek chci z webu scrapovat. Toto nastavení je zde kvůli tomu, že kdybych pokaždé scrapoval všechno zabralo by to moc času. <br>
Ve funkci tedy nejdříve přijdu na stránku, vytvořím si prázdný [ ] results, kam budu ukládat veškeré výsledky. Poté co přijdu na stránku, přes půlku obrazovky na mě vyskočí prompt ohledně cookies, který v případě, že se na stránce nechá dělá potíže, jelikož překrývá některé elementy. Proto hned po načtení stránky cookies odmítnu. Dále přejdu do kategorie koně. <br>
Nyní začíná první loop while, která se opakuje dokud se nedostaneme na námi nastavený počet stránek. Zde si pomocí find_elements vypíšu všechny inzeráty, které na této stránce jsou. Poté začíná vnořený for loop. <br>
```python
for itemId in range(len(items)):
            items = driver.find_elements(By.CSS_SELECTOR, ".inzeraty")
            items[itemId].find_element(By.CSS_SELECTOR,".nadpis a").click()
```
Tento loop je udělaný takto, přes indexy, jelikož pokaždé když se z inzerátu přesunu zpátky na stránku předtím, změní se ty identifikátory ze selenia. Proto jsem to obešel tím způsobem, že se pokaždé vrátím na inzerát, který je zrovna na řadě přes index.<br>
Tento loop poté pro každý inzerát vyscrapuje požadované hodnoty pomocí find element.text, čímž zpátky získám textový řetězec. Pro jasně identifikovatelné elementy přes css_selector, jsem použil css selector, pro méně jasné jsem využil xpath, kde jsem jednotlivé cesty získal pomocí rozšíření do firefoxu [xPath Finder](https://addons.mozilla.org/en-US/firefox/addon/xpath_finder/). <br>
Atributy, které jsem scrapoval byly: 
 - ad_name - název inzerátu (h1)
 - price - cena uvedená u inzerátu
 - contact_name - kontaktní osoba uvedená u inzerátu
 - contact number - číslo na kontaktní osobu (zde se číslo objevuje ve špatném formátu 728... zobraz číslo, protože pro zobrazení čísla je třeba nejdřve ověřit své číslo na stránce)
 - contact_locality - lokalita uvedená u inzerátu
 - ad_date - datum vytvoření inzerátu - scrapuje se ve tvaru *- HOT(optional) - [datum]* proto zde využívám funkci *.split("[")[-1]*, což mi vrátí *datum]* a proto ještě odstraním poslední znak pomocí:
 *ad_date[:-1].strip()*
 - ad_text - v poslední řadě vracím předmět inzerátu, kde jsou napsány další informace o inzerátu (jedná se o souvislý text) <br>

Dle zadání by zde měli být ještě: věk koně, barva, plemeno, výška kohoutku (KVH). Jenže tyto atributy nemají v inzerátu žádný specifický identifikátor a jsou jako plain text napsány v ad_text. Navíc každý kdo vytváří inzerát tak si to píše podle sebe, což znamená že i kdybych použil regulární výrazy, vysledky by byly mizerné. <br>
Pro příklad zde uvedu následující: 
- věk koně je zde pokaždé v jiném formátu, někdo do textu napsal narozen, narodený, nar.,*2015, věk, a další možné variace (to jsem procházel jen první 2 stránky)
- u barvy většinou chyběla, občas někdo napsal že prodává černého koně, ale toto není dostatečný identifikátor, který by přinesl nějaké zdárné výsledky při použití regulárních výrazů
- u plemene se již vůbec nemají regulární výrazy za co přichytit
- kvh si taky každý psal jak chtěl, někdo napsal kvh je asi, někdo 126 kvh, někdo napsal zase výšku a někdo před napsáním číslu u kvh použil několik vycpávkových slov

Mým nápadem jak tento problém vyřešit by bylo využití nějakého LLM modelu přes knihovnu replicate například [MistralAi](https://replicate.com/mistralai/mistral-7b-instruct-v0.2), ale proto aby se využilo přes API je třeba získat token, který je schovaný za registrací a také za paywallem. Navíc dle instrukcí, v zadání nebylo povoleno využívat "Chat GPT a obdobné AI pomocníky". Tento LLM model bych poté promptoval aby mi z plain textu získal jednotlivé atributy pokud je najde a vrátí mi je v nějaké přijatelné podobě, která by se pak dala rozdělit do DF do jednotlivých sloupců. <br>
Poté co získám všechna data pro jeden inzerát uložím pomocí append do results v podobě tuple (ad_name,price,contact_name,contact_number,contact_locality, ad_date,ad_text) <br>
Po provedení celé for loop pro současnou stránku přejde skript na try except blok, který v případě že na stránce existuje proklik na další stránku přesune se na ni, pokud ne díky except NoSuchElementException vyskočí z while loop a ukončí prohlížeč <br>
Nakonec celá funkce vrátí naplněný list s results.
### Funkce send_email(config_file)
Tato funkce má za úkol vzít config_file jako argument, načíst z něj data a podle nich poté odeslat email dle instrukcí z configu. <br>
V prvé řadě si tedy zavolám configparser a přečtu config, tento config je rozdělen do 4 sekcí, z toho 3 sekce patří k emailu. První sekce SMTP získává smtp adresu emailového serveru a jeho port. Další sekce authentication bere přihlašovací údaje do emailu ze kterého budu posílat emailovou zprávu posílat. V mém případě posílám email ze serveru google.com. Pokud máte u google nastavený 2FA a nebo jiné další ověřovací metody je třeba nejdříve přejít na stránky googlu [My Account -App Passwords](https://myaccount.google.com/u/0/apppasswords) a zde si vygenerovat heslo, kterým poté aplikace bude přistupovat k emailu. Poslední sekce je EMAIL_CONTENTS, kde se specifikují příjemci, odesílatel, předmět emailu, zpráva a  cestu k příloze, kterou chceme spolu s emailem poslat<br>
Pro sestavení emailu využívám funkci emailMessage() z knihovny email.message. Zde postupně zadám proměnné z configu a tím sestavím emailovou zprávu. <br>
Poté následuje try except blok, který pomocí knihovny smtplib nejdříve začne přenos pomocí smtp adresy a portu, poté pošle handshake a poté se pokusí přihlásit. Pokud přihlášení proběhne úspěšně v konzoli se objeví Connection successful. Poté pokud vše proběhne bez problému odešle se email, při chybě by to spadlo do exception a vypsalo by to chybu, která nastala. <br>
### Funkce scrape_then_send_email()
Toto je pomocná funkce, pomocí které si připravím a spustím obě předchozí funkce, takto je to vyrobené aby se potom mohla funkce poslat do schedule.do() <br>
Nejdříve si tedy nadefinuji jaký prohlížeč budu ke scrapovaní používat (v mém případě se jednalo o Firefox), přidám url a poté už zavolám funkci scraper() do proměnné results <br>
Z results si poté udělám pomocí pandas dataframe, kterému také nadefinuji záhlaví a ten outputnu do csv "output.csv". <br>
V poslední řadě zavolám funkci send_email("settings.config") s cestou k mému configu.
### Funkce main()
Ve funkci main řeším scheduling skriptu a to aby se executoval v předem definovaný čas podle settings.config. Na to mám část configu SCHEDULE, kde si mohu nastavit interval (day, monday, tuesday, wednesday, thursday, friday, saturday, sunday), který říká jak často se bude skript pouštět, vždy před každý interval si představte every (viz. interval every day). A poté se zde nastavuje čas, který říká v kolik se bude skript pouštět. Z toho pak tedy vznikne že se skript bude pouštět například: every day at 18:00. <br>
Nejdříve si tedy načtu proměnné z configu a poté podle jednoduché if elif logiky zjištuji v jakém intervalu chci skript pouštět. Poté pomocí knihovny schedule dám, že chci pouštět skript every INTERVAL at TIME spustit funkci scrape_then_send_email() <br>
Nakonci je pak while loop, která nekonečně dokola každou sekundu pouští schedule.run_pending() ,který kontroluje zda je čas spustit nějaký skript podle dané schedule.
## Prerequisities
Pro správné fungování kódu je třeba mít nainstalované následující knihovny
```batch
pip install selenium
pip install pandas
pip install schedule
```
