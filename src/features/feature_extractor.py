import re
import requests
from bs4 import BeautifulSoup
import ipaddress
# import whois # Pastikan library 'whois' atau 'python-whois' terinstal
from datetime import datetime, timezone
from urllib.parse import urlparse
import socket
import logging

logger = logging.getLogger("FeatureExtractor")

# Helper function for feature_extractor
def diff_month(d1, d2):
    if isinstance(d2, list):
        valid_dates = [d for d in d2 if hasattr(d, 'year')]
        if valid_dates:
            d2 = min(valid_dates)
        else:
            return -1
    
    if d2 is None or not hasattr(d2, 'year'):
        return -1
        
    return (d1.year - d2.year) * 12 + d1.month - d2.month

def extract_features(url_input):
    logger.info(f"Memulai ekstraksi fitur untuk URL: {url_input}")
    data_set = []
    current_url = url_input
    
    if not re.match(r"^https?", current_url):
        current_url = "http://" + current_url 
        logger.debug(f"URL dinormalisasi menjadi: {current_url}") 

    response = ""
    soup = -999
    try:
        logger.debug(f"Mencoba mengambil konten dari URL: {current_url}")
        response = requests.get(current_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        logger.debug(f"Berhasil mengambil konten dari URL: {current_url}")
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error saat mengambil URL '{current_url}': {http_err}")
    except requests.exceptions.ConnectionError as conn_err:
        logger.error(f"Connection error saat mengambil URL '{current_url}': {conn_err}")
    except requests.exceptions.Timeout as timeout_err:
        logger.error(f"Timeout saat mengambil URL '{current_url}': {timeout_err}")
    except requests.exceptions.RequestException as req_err:
        logger.error(f"Error lain (requests) saat mengambil URL '{current_url}': {req_err}")
    except Exception as e:
        logger.error(f"Error umum saat memproses respons atau parsing HTML untuk URL '{current_url}': {e}")

    domain = ""
    try:
        domain_match = re.findall(r"://([^/]+)/?", current_url)
        if domain_match:
            domain = domain_match[0]
            if re.match(r"^www.",domain):
                domain = domain.replace("www.","")
            logger.debug(f"Domain diekstrak: '{domain}' dari URL: '{current_url}'")
        else:
            logger.warning(f"Tidak dapat mengekstrak domain dari URL: '{current_url}'")
    except Exception as e:
        logger.error(f"Error saat mengekstrak domain dari URL '{current_url}': {e}")

    # whois_response = None
    # if domain:
    #     logger.info(f"Mencoba query WHOIS untuk domain: '{domain}' (dari URL: '{current_url}')")
    #     try:
    #         whois_data_object = whois.whois(domain)
    #         if whois_data_object:
    #             raw_text = None
    #             if hasattr(whois_data_object, 'text') and whois_data_object.text:
    #                 raw_text = whois_data_object.text
    #             elif isinstance(whois_data_object, dict) and whois_data_object.get('raw'):
    #                 raw_text_val = whois_data_object.get('raw')
    #                 raw_text = "\n".join(raw_text_val) if isinstance(raw_text_val, list) else str(raw_text_val)

    #             has_key_attributes = (hasattr(whois_data_object, 'domain_name') or 
    #                                 hasattr(whois_data_object, 'creation_date') or 
    #                                 hasattr(whois_data_object, 'status') or 
    #                                 hasattr(whois_data_object, 'emails'))
    #             is_dict_with_keys = isinstance(whois_data_object, dict) and \
    #                                 (whois_data_object.get('domain_name') or 
    #                                 whois_data_object.get('creation_date') or 
    #                                 whois_data_object.get('status') or 
    #                                 whois_data_object.get('emails'))

    #             if raw_text and ("Connection timed out" in raw_text or "error" in raw_text.lower() or "limit" in raw_text.lower() or "not found" in raw_text.lower() or "no match" in raw_text.lower()):
    #                 logger.error(f"WHOIS query untuk '{domain}' berhasil, TAPI teks respons mengindikasikan masalah: {raw_text[:150]}")
    #                 whois_response = None
    #             elif has_key_attributes or is_dict_with_keys:
    #                 logger.info(f"WHOIS query untuk domain '{domain}' (dari URL '{current_url}') berhasil dan tampak valid.")
    #                 whois_response = whois_data_object
    #             else:
    #                 logger.warning(f"WHOIS query untuk '{domain}' mengembalikan objek/dict, tapi tampak tidak lengkap atau tidak valid: {str(whois_data_object)[:200]}")
    #                 whois_response = None
    #         else:
    #             logger.warning(f"WHOIS query untuk domain '{domain}' (dari URL '{current_url}') langsung mengembalikan None.")
    #             whois_response = None
    #     except Exception as e:
    #         error_message = str(e)
    #         if "No match for" in error_message or "not found" in error_message.lower():
    #             logger.info(f"Domain '{domain}' tidak ditemukan di database WHOIS (domain mungkin tidak terdaftar)")
    #         elif "timeout" in error_message.lower():
    #             logger.error(f"Timeout saat query WHOIS untuk domain '{domain}': {e}")
    #         else:
    #             logger.error(f"Error WHOIS untuk domain '{domain}': {type(e).__name__} - {e}")
    #         whois_response = None
    # else:
    #     logger.warning(f"Query WHOIS dilewati karena domain tidak berhasil diekstrak dari URL: '{current_url}'")

    # 1.IP_Address
    try:
        parsed_url_for_ip_check = urlparse(current_url)
        ipaddress.ip_address(parsed_url_for_ip_check.netloc)
        data_set.append(-1)
    except ValueError:
        data_set.append(1)
    except Exception:
        data_set.append(-1)

    # 2.URL_Length
    data_set.append(len(current_url))

    # 3. URL_Shortening
    match = re.search(
        r'1url\.com|adf\.ly|bc\.vc|bit\.do|bit\.ly|bitly\.com|bkite\.com|bl\.ink|BudURL\.com|buzurl\.com|'
        r'cli\.gs|cur\.lv|cutt\.ly|cutt\.us|db\.tt|doiop\.com|ff\.im|fic\.kr|filoops\.info|go2l\.ink|'
        r'goo\.gl|is\.gd|ity\.im|j\.mp|Just\.as|kl\.am|link\.zip\.net|lnkd\.in|loopt\.us|migre\.me|'
        r'om\.ly|ow\.ly|ping\.fm|po\.st|post\.ly|prettylinkpro\.com|q\.gs|qr\.ae|qr\.net|rebrand\.ly|'
        r'rubyurl\.com|short\.ie|short\.io|short\.to|shorte\.st|snip\.ly|snipr\.com|snipurl\.com|'
        r'scrnch\.me|su\.pr|t\.co|t2m\.io|tiny\.cc|tinyurl\.com|to\.ly|tr\.im|tweez\.me|twit\.ac|'
        r'twitthis\.com|twurl\.nl|u\.bb|u\.to|url4\.eu|v\.gd|vzturl\.com|wp\.me|x\.co|yfrog\.com|yourls\.org',
        current_url
    )
    if match:
        data_set.append(-1)
    else:
        data_set.append(1)

    # 4.Double_Slash_Redirect_After_HTTPS
    slash_indices = [match.start() for match in re.finditer('//', current_url)]
    if not slash_indices:
        data_set.append(1)
    elif slash_indices[-1] > 6:
        data_set.append(-1)
    else:
        data_set.append(1)

    # 5.Hyphen_in_Domain_Name
    if domain and "-" in domain:
        data_set.append(-1)
    else:
        data_set.append(1)

    # 6. Presence_of_Subdomain (Count of dots)
    data_set.append(current_url.count('.'))

    # 7.Uses_HTTPS_Protocol
    if current_url.startswith('https://'):
        if response == "" or response.status_code != 200:
            data_set.append(1) # HTTPS tapi masalah koneksi (bisa dipertimbangkan 0 atau -1 juga)
        else:
            data_set.append(1)
    else:
        data_set.append(-1)

    # # 8.Domain_Expiration_Remaining
    # def make_aware(dt):
    #     if dt is None:
    #         return None
    #     if dt.tzinfo is None:
    #         return dt.replace(tzinfo=timezone.utc)
    #     else:
    #         return dt.astimezone(timezone.utc)

    # if whois_response and hasattr(whois_response, 'expiration_date'):
    #     whois_expiration_date_val = whois_response.expiration_date
    #     try:
    #         processed_expiration_date = None
    #         if whois_expiration_date_val is None:
    #             domain_reg_len_feature = -1
    #         else:
    #             if isinstance(whois_expiration_date_val, list):
    #                 valid_dates = [make_aware(d) for d in whois_expiration_date_val if isinstance(d, datetime)]
    #                 if valid_dates:
    #                     processed_expiration_date = min(valid_dates)
    #             elif isinstance(whois_expiration_date_val, datetime):
    #                 processed_expiration_date = make_aware(whois_expiration_date_val)

    #             if processed_expiration_date is None:
    #                 domain_reg_len_feature = -1
    #             else:
    #                 today = datetime.now(timezone.utc)
    #                 time_difference = processed_expiration_date - today
    #                 registration_length_days = time_difference.days

    #                 if registration_length_days <= 365:
    #                     domain_reg_len_feature = -1
    #                 else:
    #                     domain_reg_len_feature = 1
    #     except (TypeError, ValueError) as e:
    #         logger.warning(f"Error processing domain expiration for {domain}: {e}")
    #         domain_reg_len_feature = -1
    #         registration_length_days = -1
    #     except Exception as e:
    #         logger.error(f"Unexpected error for domain expiration {domain}: {e}")
    #         domain_reg_len_feature = -1
    #         registration_length_days = -1
    # else:
    #     domain_reg_len_feature = -1
    #     registration_length_days = 0
    # data_set.append(registration_length_days)

    # 9.Favicon_Source_Consistency
    favicon_feature_value = -1
    if soup != -999:
        try:
            favicon_link_tags = soup.find_all(
                'link',
                attrs={'rel': re.compile(r'^(shortcut\s+)?icon$', re.I), 'href': True}
            )
            if favicon_link_tags:
                first_favicon_href = favicon_link_tags[0].get('href')
                if first_favicon_href:
                    parsed_favicon_url = urlparse(first_favicon_href)
                    if parsed_favicon_url.scheme and parsed_favicon_url.netloc:
                        favicon_hostname = parsed_favicon_url.netloc
                        if favicon_hostname.startswith("www."):
                            favicon_hostname = favicon_hostname.replace("www.", "", 1)
                        if domain and favicon_hostname == domain:
                            favicon_feature_value = 1
                    else: 
                        favicon_feature_value = 1 
            # else: favicon_feature_value = 1 # Jika tidak ada favicon eksplisit, bisa dianggap aman
        except Exception as e:
            logger.warning(f"Error processing favicon for {current_url}: {e}")
            pass
    data_set.append(favicon_feature_value)

    # 10. Custom_Port_Usage
    port_feature_value = 1
    try:
        parsed_url_for_port_check = urlparse(current_url)
        if parsed_url_for_port_check.port:
            if parsed_url_for_port_check.scheme == 'http' and parsed_url_for_port_check.port == 80:
                port_feature_value = 1
            elif parsed_url_for_port_check.scheme == 'https' and parsed_url_for_port_check.port == 443:
                port_feature_value = 1
            else: 
                port_feature_value = -1
    except ValueError: 
        port_feature_value = -1
    except Exception:
        port_feature_value = -1
    data_set.append(port_feature_value)

    # 11.External_Resource_Ratio
    num_total_resources = 0
    num_same_domain_resources = 0
    # request_url_feature_value = 1 # Logika lama untuk nilai -1, 0, 1

    if soup == -999:
        # request_url_feature_value = -1
        data_set.append(-1.0) # Indikasi error atau tidak bisa dihitung
    else:
        all_resource_elements = []
        src_based_tags = ['img', 'script', 'iframe', 'embed', 'audio', 'video', 'source', 'track', 'frame']
        for tag_name in src_based_tags:
            all_resource_elements.extend(soup.find_all(tag_name, src=True))
        all_resource_elements.extend(soup.find_all('object', data=True))
        all_resource_elements.extend(soup.find_all('input', type='image', src=True))
        all_resource_elements.extend(soup.find_all('link', rel='stylesheet', href=True))

        for tag_object in all_resource_elements:
            resource_url_str = None
            if tag_object.name == 'object':
                resource_url_str = tag_object.get('data')
            elif tag_object.name == 'link':
                resource_url_str = tag_object.get('href')
            else:
                resource_url_str = tag_object.get('src')

            if not resource_url_str:
                continue

            num_total_resources += 1
            is_same_domain = False
            parsed_resource_url = urlparse(resource_url_str)

            if parsed_resource_url.scheme and parsed_resource_url.netloc:
                resource_hostname = parsed_resource_url.netloc
                if resource_hostname.startswith("www."):
                    resource_hostname = resource_hostname.replace("www.", "", 1)
                if domain and resource_hostname == domain:
                    is_same_domain = True
            else: 
                is_same_domain = True

            if is_same_domain:
                num_same_domain_resources += 1
        
        percent_same_domain_resources = 100.0 if num_total_resources == 0 else (num_same_domain_resources / float(num_total_resources)) * 100
        data_set.append(round(percent_same_domain_resources, 2))
        # Logika lama untuk nilai -1, 0, 1
        # if num_total_resources > 0:
        #     percent_same_domain = (num_same_domain_resources / float(num_total_resources)) * 100
        #     if percent_same_domain < 40.0: request_url_feature_value = -1
        #     else: request_url_feature_value = 1
        # data_set.append(request_url_feature_value)


    # 12.External_Links_Ratio
    num_total_anchors = 0
    num_unsafe_anchors = 0
    # anchor_feature_value = 1 # Logika lama

    if soup == -999:
        # anchor_feature_value = -1
        data_set.append(-1.0) # Indikasi error
    else:
        for a_tag in soup.find_all('a', href=True):
            num_total_anchors += 1
            is_anchor_unsafe = False
            anchor_href = a_tag.get('href', '').strip()
            anchor_href_lower = anchor_href.lower()

            if not anchor_href or \
                anchor_href_lower.startswith('#') or \
                anchor_href_lower.startswith('javascript:') or \
                anchor_href_lower.startswith('mailto:'):
                is_anchor_unsafe = True
            else:
                parsed_anchor_url = urlparse(anchor_href)
                if parsed_anchor_url.scheme.lower() in ['http', 'https'] and parsed_anchor_url.netloc:
                    anchor_hostname = parsed_anchor_url.netloc
                    if anchor_hostname.startswith("www."):
                        anchor_hostname = anchor_hostname.replace("www.", "", 1)
                    if domain and anchor_hostname != domain:
                        is_anchor_unsafe = True
            if is_anchor_unsafe:
                num_unsafe_anchors += 1
        
        percent_unsafe_anchors = 0.0 if num_total_anchors == 0 else (num_unsafe_anchors / float(num_total_anchors)) * 100 # Mengembalikan 0 jika tidak ada anchor, bukan 100
        data_set.append(round(percent_unsafe_anchors, 2))
        # Logika lama
        # if num_total_anchors > 0:
        #     percentage_unsafe_anchors = (num_unsafe_anchors / float(num_total_anchors)) * 100
        #     if percentage_unsafe_anchors < 50.0: anchor_feature_value = 1
        #     else: anchor_feature_value = -1
        # data_set.append(anchor_feature_value)

    # 13.External_CSS_and_JS_Resources
    num_total_links_scripts = 0
    num_same_domain_links_scripts = 0
    # links_in_tags_feature_value = 1 # Logika lama

    if soup == -999:
        # links_in_tags_feature_value = -1
        data_set.append(-1.0) # Indikasi error
    else:
        for link_tag in soup.find_all('link', rel='stylesheet', href=True):
            num_total_links_scripts += 1
            resource_url_str = link_tag.get('href')
            if not resource_url_str: continue
            is_same_domain = False
            parsed_resource_url = urlparse(resource_url_str)
            if parsed_resource_url.scheme and parsed_resource_url.netloc:
                resource_hostname = parsed_resource_url.netloc
                if resource_hostname.startswith("www."): resource_hostname = resource_hostname.replace("www.", "", 1)
                if domain and resource_hostname == domain: is_same_domain = True
            else: is_same_domain = True
            if is_same_domain: num_same_domain_links_scripts += 1

        for script_tag in soup.find_all('script', src=True):
            num_total_links_scripts += 1
            resource_url_str = script_tag.get('src')
            if not resource_url_str: continue
            is_same_domain = False
            parsed_resource_url = urlparse(resource_url_str)
            if parsed_resource_url.scheme and parsed_resource_url.netloc:
                resource_hostname = parsed_resource_url.netloc
                if resource_hostname.startswith("www."): resource_hostname = resource_hostname.replace("www.", "", 1)
                if domain and resource_hostname == domain: is_same_domain = True
            else: is_same_domain = True
            if is_same_domain: num_same_domain_links_scripts += 1
        
        percent_same_domain_css_js = 100.0 if num_total_links_scripts == 0 else (num_same_domain_links_scripts / float(num_total_links_scripts)) * 100
        data_set.append(round(percent_same_domain_css_js, 2))
        # Logika lama
        # if num_total_links_scripts > 0:
        #     percentage_same_domain = (num_same_domain_links_scripts / float(num_total_links_scripts)) * 100
        #     if percentage_same_domain < 50.0: links_in_tags_feature_value = -1
        #     else: links_in_tags_feature_value = 1
        # data_set.append(links_in_tags_feature_value)

    # 14.External_Form_Submission
    sfh_feature_value = 1
    if soup == -999:
        sfh_feature_value = -1
    else:
        forms_with_action = soup.find_all('form', action=True)
        if forms_with_action:
            for form_tag in forms_with_action: 
                action_attribute = form_tag.get('action', '').strip()
                if not action_attribute or action_attribute.lower() == "about:blank":
                    sfh_feature_value = -1
                else:
                    parsed_action_url = urlparse(action_attribute)
                    if parsed_action_url.scheme.lower() in ['http', 'https'] and parsed_action_url.netloc:
                        action_hostname = parsed_action_url.netloc
                        if action_hostname.startswith("www."):
                            action_hostname = action_hostname.replace("www.", "", 1)
                        if domain and action_hostname != domain:
                            sfh_feature_value = -1
                break 
    data_set.append(sfh_feature_value)

    # 15.Form_Submits_to_Email_Address
    submission_to_email_feature_value = 1
    if response == "" or soup == -999:
        submission_to_email_feature_value = -1
    else:
        form_submits_to_email = False
        for form_tag in soup.find_all('form', action=True):
            action_attribute = form_tag.get('action', '').strip().lower()
            if action_attribute.startswith('mailto:'):
                form_submits_to_email = True
                break
        if form_submits_to_email:
            submission_to_email_feature_value = -1
    data_set.append(submission_to_email_feature_value)

    # 16.HTTP_Response_Status_Content
    page_content_feature_value = 0 
    if response == "":
        page_content_feature_value = -1
    elif hasattr(response, 'text'):
        if response.text == "":
            page_content_feature_value = -1
        else:
            page_content_feature_value = 1
    else:
        page_content_feature_value = -1
    data_set.append(page_content_feature_value)

    # 17.Number_of_Redirects
    # redirect_feature_value = -1 # Logika lama
    num_redirects_val = -1
    if response == "":
        # redirect_feature_value = -1
        num_redirects_val = -1 # Gagal memuat
    elif hasattr(response, 'history'):
        num_redirects_val = len(response.history)
        # Logika lama
        # if num_redirects_val <= 1: redirect_feature_value = 1
        # elif num_redirects_val >= 2 and num_redirects_val <= 4: redirect_feature_value = 0
        # else: redirect_feature_value = -1
    data_set.append(num_redirects_val) # Menyimpan jumlah redirect aktual
    # data_set.append(redirect_feature_value) # Logika lama

    # 18.Mouseover_Link_Manipulation
    on_mouseover_feature_value = 1
    if response == "" or soup == -999:
        on_mouseover_feature_value = -1
    elif hasattr(response, 'text'):
        if re.search(r"onmouseover", response.text, re.IGNORECASE):
            on_mouseover_feature_value = -1
    data_set.append(on_mouseover_feature_value)

    # 19.Right_Click_Disabled
    disable_right_click_feature_value = 1
    if response == "" or soup == -999:
        disable_right_click_feature_value = -1
    elif hasattr(response, 'text'):
        if re.search(r"oncontextmenu|event\.button\s*==\s*2|event\.which\s*==\s*3", response.text, re.IGNORECASE):
            disable_right_click_feature_value = -1
    data_set.append(disable_right_click_feature_value)

    # 20.Popup_Window_Usage
    popup_window_feature_value = 1
    if response == "" or soup == -999:
        popup_window_feature_value = -1
    elif hasattr(response, 'text'):
        if re.search(r"alert\s*\(|confirm\s*\(|prompt\s*\(|window\.open\s*\(", response.text, re.IGNORECASE):
            popup_window_feature_value = -1
    data_set.append(popup_window_feature_value)

    # 21.Iframe_Usage
    iframe_feature_value = 1
    if response == "" or soup == -999:
        iframe_feature_value = -1
    elif soup != -999 :
        if soup.find("iframe") or soup.find("frame"):
            iframe_feature_value = -1
    data_set.append(iframe_feature_value)

    # # 22.Domain_Age
    # def to_aware_utc(dt): # Helper lokal untuk fitur ini
    #     if dt is None: return None
    #     if dt.tzinfo is None: return dt.replace(tzinfo=timezone.utc)
    #     return dt.astimezone(timezone.utc)

    # # domain_age_feature_value = -1 # Logika lama
    # actual_creation_date = None
    # domain_age_months_val = -1 # Default jika tidak bisa dihitung

    # if whois_response and hasattr(whois_response, 'creation_date'):
    #     creation_date_data = whois_response.creation_date
    #     if isinstance(creation_date_data, list):
    #         aware_dates = [to_aware_utc(d) for d in creation_date_data if isinstance(d, datetime)]
    #         if aware_dates: actual_creation_date = min(aware_dates)
    #     elif isinstance(creation_date_data, datetime):
    #         actual_creation_date = to_aware_utc(creation_date_data)
    
    # current_time = datetime.now(timezone.utc)
    # try:
    #     if actual_creation_date:
    #         age_months = diff_month(current_time, actual_creation_date)
    #         domain_age_months_val = age_months
    #         # Logika lama
    #         # if age_months >= 6: domain_age_feature_value = 1
    #         # else: domain_age_feature_value = -1
    #     # else: domain_age_feature_value = -1 # Logika lama
    # except Exception as e:
    #     logger.error(f"Error calculating domain age for {domain}: {e}")
    #     # domain_age_feature_value = -1 # Logika lama
    #     domain_age_months_val = -1 # Error
    # data_set.append(domain_age_months_val) # Menyimpan usia domain dalam bulan
    # # data_set.append(domain_age_feature_value) # Logika lama

    # # 23.Whois_Data_Availability_and_Expiry
    # dns_record_feature = -1 
    # if whois_response and (getattr(whois_response, 'domain_name', None) or isinstance(whois_response.get('domain_name'), (str, list)) ): # Cek lebih fleksibel
    #     if domain_reg_len_feature == 1: 
    #         dns_record_feature = 1
    #     else: 
    #         dns_record_feature = -1
    # else: 
    #     dns_record_feature = -1
    # data_set.append(dns_record_feature)
    
    # 24.URL_Blacklist_Status
    suspicious_url_patterns = r'at\.ua|usa\.cc|baltazarpresentes\.com\.br|pe\.hu|esy\.es|hol\.es|sweddy\.com|myjino\.ru|96\.lt|ow\.ly'
    suspicious_ip_patterns = (
        r'146\.112\.61\.108|213\.174\.157\.151|121\.50\.168\.88|192\.185\.217\.116|78\.46\.211\.158|181\.174\.165\.13|46\.242\.145\.103|121\.50\.168\.40|83\.125\.22\.219|46\.242\.145\.98|'
        r'107\.151\.148\.44|107\.151\.148\.107|64\.70\.19\.203|199\.184\.144\.27|107\.151\.148\.108|107\.151\.148\.109|119\.28\.52\.61|54\.83\.43\.69|52\.69\.166\.231|216\.58\.192\.225|'
        r'118\.184\.25\.86|67\.208\.74\.71|23\.253\.126\.58|104\.239\.157\.210|175\.126\.123\.219|141\.8\.224\.221|10\.10\.10\.10|43\.229\.108\.32|103\.232\.215\.140|69\.172\.201\.153|'
        r'216\.218\.185\.162|54\.225\.104\.146|103\.243\.24\.98|199\.59\.243\.120|31\.170\.160\.61|213\.19\.128\.77|62\.113\.226\.131|208\.100\.26\.234|195\.16\.127\.102|195\.16\.127\.157|'
        r'34\.196\.13\.28|103\.224\.212\.222|172\.217\.4\.225|54\.72\.9\.51|192\.64\.147\.141|198\.200\.56\.183|23\.253\.164\.103|52\.48\.191\.26|52\.214\.197\.72|87\.98\.255\.18|209\.99\.17\.27|'
        r'216\.38\.62\.18|104\.130\.124\.96|47\.89\.58\.141|78\.46\.211\.158|54\.86\.225\.156|54\.82\.156\.19|37\.157\.192\.102|204\.11\.56\.48|110\.34\.231\.42'
    )
    blocklist_feature_value = 1
    if re.search(suspicious_url_patterns, current_url):
        blocklist_feature_value = -1
    elif domain:
        try:
            ip_address_str = socket.gethostbyname(domain)
            if re.search(suspicious_ip_patterns, ip_address_str):
                blocklist_feature_value = -1
        except socket.gaierror:
            logger.warning(f"DNS resolution failed for domain {domain} in blacklist check.")
            blocklist_feature_value = -1 
        except Exception as e:
            logger.error(f"Error resolving IP for domain {domain} in blacklist check: {e}")
            blocklist_feature_value = -1
    elif not domain:
        blocklist_feature_value = -1
    data_set.append(blocklist_feature_value)

    # # 25.Domain_Registration_Entity
    # domain_registered_by_company_value = -1
    # if whois_response:
    #     try:
    #         registrant_organization = whois_response.get('org') or \
    #                                 whois_response.get('organization') or \
    #                                 getattr(whois_response, 'org', None) or \
    #                                 getattr(whois_response, 'organization', None) or \
    #                                 whois_response.get('registrant_organization')

    #         if registrant_organization: # Tidak null dan tidak string kosong implisit
    #             registrant_organization_str = ""
    #             if isinstance(registrant_organization, list):
    #                 registrant_organization_str = str(registrant_organization[0]).strip() if registrant_organization else ""
    #             elif isinstance(registrant_organization, str):
    #                  registrant_organization_str = registrant_organization.strip()
                
    #             if registrant_organization_str: # Setelah diproses, pastikan tidak kosong
    #                 known_privacy_phrases = ["privacy", "proxy", "whoisguard", "domains by proxy", "contact privacy", "private registration", "redacted for privacy", "identity protected", "domain protection services", "perfect privacy", "anonymous"]
    #                 is_privacy_service = False
    #                 org_lower = registrant_organization_str.lower()
    #                 for phrase in known_privacy_phrases:
    #                     if phrase in org_lower:
    #                         is_privacy_service = True
    #                         break
    #                 if is_privacy_service:
    #                     domain_registered_by_company_value = -1
    #                 else:
    #                     # Minimal check: panjang string > 2 (menghindari inisial atau karakter acak)
    #                     # dan tidak hanya angka (menghindari ID numerik)
    #                     if len(registrant_organization_str) > 2 and not registrant_organization_str.isdigit():
    #                          domain_registered_by_company_value = 1
    #                     # else tetap -1
    #             # else: 'org' kosong setelah strip, tetap -1
    #     except AttributeError: 
    #         domain_registered_by_company_value = -1
    #     except Exception as e:
    #         logger.warning(f"Error processing company registration for {domain}: {e}")
    #         domain_registered_by_company_value = -1
    # data_set.append(domain_registered_by_company_value)

    logger.info(f"Selesai ekstraksi fitur untuk URL: {current_url}. Total fitur: {len(data_set)}")
    return data_set