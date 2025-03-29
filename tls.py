def fetch_related_tlds_and_domains(domain):
	"""
	Fetch related TLDs and domains using TLSx.
	related domains are those that are not part of related TLDs.
	
	Args:
		domain (str): The domain to find related TLDs and domains for.
	
	Returns:
		tuple: A tuple containing two lists (related_tlds, related_domains).
	"""
	print(f"Fetching related TLDs and domains for {domain}")
	related_tlds = set()
	related_domains = set()
	
	# Extract the base domain
	extracted = tldextract.extract(domain)
	base_domain = f"{extracted.domain}.{extracted.suffix}"
	
	cmd = f'tlsx -san -cn -silent -ro -host {domain}'
	_, result = run_command(cmd, shell=True)

	for line in result.splitlines():
		try:
				line = line.strip()
				if line == "":
					continue
				extracted_result = tldextract.extract(line)
				full_domain = f"{extracted_result.domain}.{extracted_result.suffix}"
				
				if extracted_result.domain == extracted.domain:
					if full_domain != base_domain:
						related_tlds.add(full_domain)
				elif extracted_result.domain != extracted.domain or extracted_result.subdomain:
					related_domains.add(line)
		except Exception as e:
			print(f"An error occurred while fetching related TLDs and domains for {domain}: {str(e)}")
			continue
	
	print(f"Found {len(related_tlds)} related TLDs and {len(related_domains)} related domains for {domain}")
	return list(related_tlds), list(related_domains)


