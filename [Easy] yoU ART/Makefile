flag:
	@echo [+] Flag : $$(cd challenge; python3 -c 'from secret import FLAG; print(FLAG);')

solver:
	@echo [+] Running solver
	@echo $$(cd htb ; python solver.py)

test: flag solver
