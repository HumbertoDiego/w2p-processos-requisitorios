import sys, psycopg2
def pop(**kargs):
    print(user,senha)
    con = psycopg2.connect("dbname=authdb user=%s password=%s"%(user,senha))
    cur = con.cursor()

    cur.execute("INSERT INTO secao (nm_sigla, in_excluido) VALUES (%s,%s) RETURNING id_secao;", ("Chefia","n"))
    id_secao = cur.fetchone()[0]
    cur.execute("INSERT INTO secao (id_pai,nm_sigla, in_excluido) VALUES (%s,%s,%s) RETURNING id_secao;", (id_secao,"Aquisições","n"))
    cur.execute("INSERT INTO usuario (nm_usuario, in_excluido) VALUES (%s,%s) RETURNING id_usuario;", ("Chefe SALC", "n"))
    id_usuario = cur.fetchone()[0]
    cur.execute("INSERT INTO pessoa (nm_login, nm_completo, cd_patente, nm_guerra) VALUES (%s,%s,%s,%s) RETURNING id_pessoa", ("capdiego", "Humberto Diego Aguiar Alves", "6", "Diego"))
    id_pessoa = cur.fetchone()[0]
    cur.execute("INSERT INTO usuario_pessoa (id_usuario, id_pessoa) VALUES (%s,%s)", (id_usuario, id_pessoa))
    cur.execute("INSERT INTO usuario_secao (id_usuario, id_secao) VALUES (%s,%s)", (id_usuario, id_secao))

    con.commit()
    print(id_secao,id_pessoa,id_usuario)
    # Close communication with the database
    cur.close()
    con.close()



if __name__ == '__main__':
    user = "postgres"
    senha = "secret"
    if len(sys.argv)==2:
        senha = sys.argv[1]
    elif len(sys.argv)>2:
        user = sys.argv[1]
        senha = sys.argv[2]
    pop(user=user, senha=senha)