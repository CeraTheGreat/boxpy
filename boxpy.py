import src.boxapi as boxapi

repl = boxapi.BoxRepl()
repl.prompt = '>'
repl.cmdloop('starting prompt...')
