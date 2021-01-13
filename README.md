#  YEDB specifications

Version: **1**

## 1. General

- YEDB is the database format / engine, designed to store configuration files
  and other reliable data.

- YEDB is designed for reliability: the data survive any power loss, unless the
  file system is broken.

- YEDB is the data serialization / storage engine, used by
  [AlterTech](https://www.altertech.com) in industrial and embedded software
  products.

- YEDB has the free data format which can be used under Apache 2.0 software
  license.

- YEDB uses a very simple data format: keys are stored as serialized regular
  files. The format helps the database survive disasters and is highly
  repairable.

- YEDB libraries and client / server implementations are free, open-source and
  provided under Apache 2.0 software license.

## 1.1 Implementations

- [yedb-py](https://github.com/alttch/yedb-py) - Python library and
  client/server.

## 1.2 References

The following third-party technologies are mentioned in this document:

- JSON: https://www.json.org

- MessagePack: https://msgpack.org

- CBOR: https://cbor.io 

- YAML: https://yaml.org

- JSON RPC: https://www.jsonrpc.org

- JSON Schema: https://json-schema.org

## 2. Database format

### 2.1 Common

- all meta date/time values are represented as UNIX timestamps in nanoseconds
  (unsigned 64-bit integer).

- all integer numbers are stored with little-endian order.

### 2.2 Meta information file

The file MUST be called ".yedb" and stored in the database root directory. The
file MUST be serialized as JSON and contain the following fields:

| Name      | Type   | Description                    |
| --------- | ------ | ------------------------------ |
| fmt       | String | data serialization format code |
| created   | u64    | database creation timestamp    |
| version   | u16    | engine version                 |
| checksums | bool   | data storage checksums enabled |

### 2.3 Key files

#### 2.3.1 General

Key files MUST be stored in regular files. The format MUST be kept to allow
system administrators repair a database without any external tools. The full
path tree, where a key file is stored, MUST represent the key full name.

Example: a key, named "my/cool/key" should be:

- stored in "my/cool" directory

- named "key" with the extension, representing the data serialization format

- keys, which have the path starting with dot (".") are considered as hidden

When deleted, the engine SHOULD automatically remove unnecessary directories in
the path tree.

The root key SHOULD NOT have any value. Other "parent" keys MAY have values set.

#### 2.3.2 File format

The database can have files of the same format only. Checksums are enabled or
disabled globally, for all keys in the database.

##### 2.3.2.1 Checksums disabled

If checksums are disabled, key files contain serialized data as-is. This is
more easy for manually repairing the database, but less reliable for data
integrity.

##### 2.3.2.2 Checksums enabled

###### 2.3.2.2.1 Binary serialization formats

| Byte range | Size | Value                               |
| ---------- | ---- | ----------------------------------- |
| 0-31       | 32   | SHA256-checksum of serialized data  |
| 32-39      | 8    | Set timestamp                       |
| 40-        |      | Serialized data                     |

###### 2.3.2.2.2 Text serialization formats

| String | Value                    
| ------ | ------------------------------------------- |
| 1      | SHA256-checksum of serialized data (HEX)    |
| 2      | Set timestamp (hex)                         |
| 3-N    | Serialized data                             |

- the strings MUST have no white spaces

- the file MUST have UNIX (new line = LF) encoding

- the serialized data SHOULD have LF ending to let key files be edited with
  regular text editors.

### 2.4 Data serialization

#### 2.4.1 Data formats

The current YEDB specifications document defines the following serialization
formats:

| Name    | Code | Mandatory  | File suffix | With c-sums | Type   |
| ------- | ---- | ---------- | ----------- | ----------- | ------ |
| json    | 1    | Y(default) | .json       | .jsonc      | text   |
| msgpack | 2    | Y          | .mp         | .mpc        | binary |
| cbor    | 3    | N          | .cb         | .cbc        | binary |
| yaml    | 4    | N          | .yml        | .ymlc       | text   |

#### 2.4.2 Data types

| Name        | Mandatory |
| ----------- | --------- |
| null        | Y         |
| boolean     | Y         |
| number      | Y         |
| string      | Y         |
| array       | Y         |
| object      | Y         |
| bytes       | N         |

The database MAY implement additional data types.

#### 2.4.3 Data type schemas

The database MAY implement strict type / structure checking for keys.

If implemented, the implementation MUST satisfy the following requirements:

- Key schemas are defined as *.schema/path/to/key* or *.schema/path* keys.

- A schema MUST be applied to individual keys or to all their sub keys, unless
  the lower-level schema is defined. E.g. the schema named *.schema/group1* is
  applied to all *group1* keys, unless some key *group1/key1* has the
  individual schema at *.schema/group1/key1*.

- The key schemas MUST implement [JSON Schema](https://json-schema.org).

- The key schemas MAY extend JSON Schema and implement additional data types.

## 3. Engine

### 3.1 Basics

- The database engine MUST support locking. Usually the locking can be performed
with an exclusively-locked file, respected by other engine instances.

- The engine MUST allow variable location of the lock file, allowing using of
  databases on read-only file systems.

- The embedded engine MUST be thread-safe out-of-the-box or provide
  documentation how to implement thread-safe usage.

- The embedded engine MAY offer asynchronous read/writes if keys are stored on
  different physical drives.

- Client/server architecture is optional.

- The engine MAY implement data caching for read operations ONLY.

- Engine methods MAY accept keys with leading slashes ("/path/to/key"), but
  MUST represent all keys without them.

#### 3.1.1 Writing and flushing data

If data flushing is enabled, the key and database data MUST be written into a
temporary file. After, the file MUST be flushed with the corresponding system
call (e.g.  *fd.flush(); libc::fsync(fd)*).

After the successful flushing:

- the key MUST be renamed to its actual name

- the key directory MUST be flushed as well

- if "write\_modified\_only" parameter is set, the engine MUST make sure the
  key value is changed before writing any data to disk.

### 3.2 Public database object variables

The database object MUST have the following variables either as public or
provide setters for them:

| Name                  | Type   | Default | Description                            |
| --------------------- | ------ | ------- | -------------------------------------- |
| auto\_repair          | bool   | true    | Auto-repair the database when opened   |
| auto\_flush           | bool   | true    | Flush key data to disk immediately     |
| lock\_ ex             | bool   | true    | Lock the database exclusively on open  |
| write\_modified\_only | bool   | true    | Write to disk modified key values only |

### 3.3 Mandatory methods

| Name                   | Args                          | Brief description                                         |
| ---------------------- | ----------------------------- | --------------------------------------------------------- |
| purge                  |                               | Remove all except keys and meta, delete broken keys       |
| safe\_purge            |                               | Same as purge but does not delete broken keys             |
| repair                 |                               | Repair broken keys, delete unrepairable                   |
| check                  |                               | Check keys                                                |
| info                   |                               | Get database info                                         |
| key\_exists            | key: String                   | Return boolean True if the key exists, False if does not  |
| key\_get               | key: String                   | Get key value                                             |
| key\_explain           | key: String                   | Get key value and extended info                           |
| key\_set               | key: String, value            | Set key value                                             |
| key\_delete            | key: String                   | Delete key                                                |
| key\_delete\_recursive | key: String                   | Delete key and all its subkeys                            |
| key\_list              | key: String                   | List key and all its subkeys Vec<String>                  |
| key\_list\_all         | key: String                   | List key and all its subkeys, including hidden            |
| key\_get\_recursive    | key: String                   | Get value of the key and all subkeys Vec\<String, Value\> |
| key\_copy              | key: String, dst\_key: String | Copy key value                                            |
| key\_rename            | key: String, dst\_key: String | Rename key / key tree                                     |
| key\_dump              | key: String                   | Get value of the key and all subkeys, ignore broken       |
| key\_load              | data: Vec\<String, Value\>    | Load dumped keys back                                     |

#### 3.3.1 Purge

The method MUST return a Generator\<String\> or an array/list of deleted broken
keys.

#### 3.3.2 Repair

The method MUST return a Generator\<(String, bool)\> or an array/list of
deleted broken keys, where bool value is *true* if the key is repaired and
*false* if the key has been deleted.

#### 3.3.3 Check

The method MUST return a Generator\<String\> or an array/list of broken keys.

#### 3.3.4 Info

The method MUST return the following data object:

| Name                | Type             | Description                                        |
| ------------------- | ---------------- | -------------------------------------------------- |
| auto\_flush         | bool             | Flush key data to disk immediately                 |
| checksums           | bool             | Checksums enabled                                  |
| created             | u64              | Database creation timestamp                        |
| fmt                 | String           | Current data serialization format                  |
| path                | bool             | Database path (server local)                       |
| repair\_recommended | bool             | Database repair is recommended (not auto-repaired) |
| server              | (String, String) | Server engine ID / Version (custom values)         |
| version             | u16              | Engine version                                     |

The object MAY contain additional fields.

#### 3.3.5 Key Explain

The method MUST return the following data object:

| Name                | Type             | Description                                                |
| ------------------- | ---------------- | ---------------------------------------------------------- |
| file                | String           | Key file                                                   |
| schema              | String           | JSON schema key if schema is defined                       |
| len                 | u64              | length for strings, objects and arrays, null for others    |
| mtime               | u64              | Key file modification timestamp                            |
| stime               | u64              | Key modification timestamp, null if checksums are disabled |
| sha256              |                  | SHA256-checksum, MUST be serialized to String              |
| type                |                  | Value type (see 2.4.2), MUST be serialized to String       |
| value               |                  | Key value                                                  |

The object MAY contain additional fields.

If the database engine has data type schemas (see 2.4.3) implemented, the
*schema* field for *.schema* keys MUST contain the value "JSON Schema VERSION",
e.g. "JSON Schema Draft-7".

If schema implements custom data types, this MUST be clearly and properly
explained. E.g. if a key schema defines that keys must contain valid Python
code, the value MUST contain either "Python" or the link to
[python.org](https://www.python.org/).

## 4. Engine API

### 4.1 Basics

The engine MUST implements [JSON RPC
2.0](https://www.jsonrpc.org/specification) API with the following conditions:

- batch requests: optional
- requests without a response required (with no "id" field): optional
- all mandatory engine methods MUST be implemented

The engine MAY implement other APIs.

### 4.2 Test

The engine MUST implement "test" method, which MUST return the following
structure:

| Name    | Type   | Description              |
| --------| ------ | ------------------------ |
| name    | String | MUST have value = "yedb" |
| version | u16    | Engine version           |

### 4.3 Server types

| Type        | Serialization formats | Notes                              |
| ----------- | --------------------- | ---------------------------------- |
| Socket      | msgpack               | TCP / UNIX socket                  |
| HTTP        | msgpack, json         | MUST respond on HTTP/POST at "/"   |

### 4.4 Binary packets format

For binary data exchange (UNIX/TCP sockets), the following format MUST be kept
for both JSON RPC API requests and responses:

| Byte range | Size | Value                                 |
| ---------- | ---- | ------------------------------------- |
| 0          | 1    | Engine version                        |
| 1          | 1    | Data format code (2 for msgpack)      |
| 2-5        | 4    | JSON RPC frame length (little-endian) |
| 6-         |      | JSON RPC request / response frame     |

### 4.5 HTTP

The HTTP transport MUST satisfy the following conditions:

- The API MUST respond to HTTP/POST requests at HTTP ROOT URI ("/")
- The API MUST accept JSON-encoded payloads by default
- The API MUST accept MessagePack-encoded payloads for requests with content
  type set to either "application/msgpack" or "application/x-msgpack".

### 4.6 JSON RPC Error codes

- Error replies SHOULD also include correct and clear error messages.

- Schema validation errors MUST return the detailed error messages.

The error codes, returned by server, MUST match the following:

### 4.6.1 Protocol errors

| Code    | Description                                    |
| ------- | -----------------------------------------------|
| -32600  | Invalid request                                |
| -32601  | Method not found                               |
| -32602  | Invalid method parameters                      |

### 4.6.2 Engine errors

| Code    | Description                                    |
| ------- | -----------------------------------------------|
| -32001  | Key not found                                  |
| -32002  | Data error, checksum error                     |
| -32003  | Schema validation error                        |
| -32004  | OS I/O errors: device errors, permissions etc. |
| -32000  | All other server errors                        |


## 5. Dump files

If the engine or a client create / load dump files, these files MUST have data
serialized with MessagePack and have the following format:

### 5.1 File header

| Byte range | Size | Value                               |
| ---------- | ---- | ----------------------------------- |
| 0          | 1    | Engine version                      |
| 1          | 1    | Data format code (2 for msgpack)    |

### 5.2 Key data

Stored starting from byte 2, for each key:

| Byte range | Size | Value                               |
| ---------- | ---- | ----------------------------------- |
| 0          | 4    | Data length                         |
| 4-         |      | Data value (msgpack)                |
