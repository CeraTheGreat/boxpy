import src.boxapi as boxapi

repl = boxapi.BoxRepl()
repl.prompt = '\nboxpy> '
repl.cmdloop('Starting prompt...')
