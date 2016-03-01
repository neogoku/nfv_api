from heat_translator_master.translator.shell import TranslatorShell

obj = TranslatorShell()
print obj._translate('tosca', 'C:\\tosca_nodejs_mongodb_two_instances.yaml', {}, True)