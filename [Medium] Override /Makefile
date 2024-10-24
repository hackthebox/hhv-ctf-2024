default:
ifdef name
	@cd challenge; \
		mkdir -p ../release/hardware_$(name); \
	 	cp client.py ../release/hardware_$(name); \
		cp log_event.c ../release/hardware_$(name);

	@cd release; \
	 	zip -9 -P hackthebox -r ./hardware_$(name).zip ./hardware_$(name); \
		unzip -l ./hardware_$(name).zip;
		
	@echo [+] Challenge was built successfully.
else
	@echo [-] Please define the challenge name. For example, \"make name=cool_chall_name\"
endif

flag:
	@echo [+] Flag : $$(cd challenge; python3 -c 'from config import FLAG; print(FLAG);')

solver:
	@echo [+] Running solver
	@echo $$(cd challenge ; python ../htb/solver.py)

test: clean default flag solver

clean:
	@rm -rf release/*
	@echo [+] Challenge release deleted successfully.
