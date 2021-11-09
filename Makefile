.PHONY: help

help: ## *:･ﾟ✧*:･ﾟ✧ This help *:･ﾟ✧*:･ﾟ✧
	@printf "\033[36;1m  %14s  \033[0;32;1m %s\033[0m\n" Target Description
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk ' \
			BEGIN {FS = ":.*?## "}; \
			{ if ( $$1 != "-") { \
			    printf "\033[31;1;40m[ \033[36;1;40m%14s \033[31;1;40m]\033[0;32;1m %s\033[0m\n", $$1, $$2 \
			   } else { \
			    printf "               \033[0;33;1m=^= %-25s =^=\033[0m\n", $$2 \
			  } \
			} \
		'

-: ## Building
###################################

clean: ## Clean build folders
	rm -r build tsmark.egg-info

pip: ## Install with pip
	pip install .

pipx: ## Install with pipx
	pipx install -f .


