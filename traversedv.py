import http.client
import re
import time
import xml.etree.ElementTree as etree
import xml as lxml

conn = http.client.HTTPSConnection('www3.discovirtual.com.ar')

def getcookie(conn) :
    conn.request("GET","/Login/Invitado.aspx")
    prehomeresp = conn.getresponse()
    prehomedata = prehomeresp.read()
    return prehomeresp.getheader("Set-Cookie").split(";")[0]

cookie = getcookie(conn)

def getcategories (conn) :
    conn.request("GET",
                 "/Comprar/Menu.aspx?IdLocal=9701&IdTipoCompra=4&Fecha=" +
                 time.strftime("%Y%m%d"),
                 None,
                 {"Cookie": cookie})
    resp = conn.getresponse()
    data = resp.read()
    data = data.replace(b"\ndocument.write(CrearMenu());",b"")
    data = data.replace(b"var ",b"")
    data = data.replace(b"new Array()",b"[]")
    data = data.replace(b"null",b"None")
    lines = data.split(b"\n")
    def dosubst(x) : return re.sub(b"\[(\d+)\]\W*=\W*new Array\(([^)]+)\)",b".append([\g<2>])",x)
    lines = list(map(dosubst,lines))
    prog = b"\n".join(lines)
    exec(prog)
    return locals()['g']

def isleafcategory(category):
    if(len(category) < 3): return False
    if(category[2]!=None): return False
    return True

def iscategorylist(category):
    if(len(category) != 3): return False
    return type(category[0]) == type(1)

def rearrangecategories(prefixes,categories) :
    if(isleafcategory(categories)):
        return [(categories[0],categories[1],prefixes)]
    else:
        if(iscategorylist(categories)):
            newprefix = prefixes.copy()
            newprefix.append(categories[1])
            return rearrangecategories(newprefix,categories[2])
        else:
            rearranged = []
            for category in categories:
                rearranged.extend(rearrangecategories(prefixes.copy(),category))
            return rearranged

cats = rearrangecategories([],getcategories(conn))            
    
def getItems (conn, idMenu) :
    conn.request("POST",
                 "/ajaxpro/_MasterPages_Home,DiviComprasWeb.ashx?method=MostrarGondola",
                 '{"idMenu": ' + str(idMenu) + '}',
                 {
                     "X-AjaxPro-Method": "MostrarGondola",
                     "User-Agent": "MyAgent",
                     "Cookie": cookie
                 }
                )
    resp = conn.getresponse()
    data = resp.read()
    data = data[1:len(data)-4]
    data = data.replace(b"\\t",b"\t")
    data = data.replace(b"\\n",b"\n")
    data = data.replace(b"\\r",b"\r")
    data = data.replace(b"\\\"",b"\"")
    return data

def processcategory(catnum) :
    items = getItems(conn, catnum)
    tree = etree.fromstring(str(items.replace(b"\r",b"").replace(b"\t",b"").replace(b"\n",b"").replace(b"&nbsp;",b"").replace(b"<BR>",b"<BR />"),'utf-8'))
    trs = tree.findall(".//tr[@class='filaListaDetalle']")
    numofitems = list(map(
        lambda x : x[8:],
        filter(
            lambda x : x.startswith("1-20 de "),
            map(
                lambda x: x.text,
                tree.findall(".//td[@class='txt-3']")
                )
            )
        ))
    pages = 1 if len(numofitems)==0 else int(int(numofitems[0])/20)
    print("Numero de paginas: {}".format(pages))
    for tr in trs:
        #lxml.etree.ElementTree.tostring(trs[0][2][0])
        nombreitem = tr[2][0].text
        unidadprecioitem = tr[2][2].text
        precio = tr[6].text
        print("Nombre: {}, Unidad {}, Precio {}".format(nombreitem,unidadprecioitem,precio))
