import 'dart:convert';
import 'dart:io';
import 'package:dio/dio.dart';
import 'package:smart_turf/config/api_config.dart';
import 'package:smart_turf/core/constants/app_constants.dart';
import 'package:smart_turf/core/exceptions/api_exception.dart';
import 'package:smart_turf/services/local/storage_service.dart';

class ApiClient {
  late Dio _dio;
  final StorageService _storageService;

  ApiClient(this._storageService) {
    _initDio();
  }

  void _initDio() {
    _dio = Dio(BaseOptions(
      baseUrl: ApiConfig.apiUrl,
      connectTimeout: Duration(milliseconds: ApiConfig.connectTimeout),
      receiveTimeout: Duration(milliseconds: ApiConfig.receiveTimeout),
      sendTimeout: Duration(milliseconds: ApiConfig.sendTimeout),
      headers: ApiConfig.defaultHeaders,
    ));

    // Interceptor pour les tokens d'authentification
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final token = await _storageService.getAuthToken();
        if (token != null && token.isNotEmpty) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        return handler.next(options);
      },
      onError: (DioException error, handler) async {
        // Gérer l'erreur 401 (token expiré)
        if (error.response?.statusCode == 401) {
          // Essayer de rafraîchir le token
          if (await _refreshToken()) {
            // Retry la requête originale
            return handler.resolve(await _retry(error.requestOptions));
          }
        }
        return handler.next(error);
      },
    ));
  }

  // Méthode pour réessayer une requête après refresh du token
  Future<Response<dynamic>> _retry(RequestOptions requestOptions) async {
    final options = Options(
      method: requestOptions.method,
      headers: requestOptions.headers,
    );

    final token = await _storageService.getAuthToken();
    options.headers?['Authorization'] = 'Bearer $token';

    return _dio.request<dynamic>(
      requestOptions.path,
      data: requestOptions.data,
      queryParameters: requestOptions.queryParameters,
      options: options,
    );
  }

  // Méthode pour rafraîchir le token d'authentification
  // Méthode pour rafraîchir le token d'authentification
  Future<bool> _refreshToken() async {
    try {
      final refreshToken = await _storageService.getRefreshToken();
      if (refreshToken == null || refreshToken.isEmpty) {
        return false;
      }

      final response = await _dio.post(
        ApiConfig.apiUrl + '/auth/refresh',
        data: {'refresh_token': refreshToken},
      );

      if (response.statusCode == 200 && response.data['success']) {
        final newToken = response.data['access_token'];
        final newRefreshToken = response.data['refresh_token'];

        await _storageService.saveAuthToken(newToken);
        await _storageService.saveRefreshToken(newRefreshToken);

        return true;
      }

      return false;
    } catch (e) {
      // Si le refresh échoue, déconnecter l'utilisateur
      await _storageService.clearAuthData();
      return false;
    }
  }

  // Méthode GET
  Future<dynamic> get(
      String endpoint, {
        Map<String, dynamic>? queryParameters,
        Options? options,
        bool requiresAuth = true, // Ajoutez ce paramètre avec une valeur par défaut
      })async {
    try {
      final response = await _dio.get(
        endpoint,
        queryParameters: queryParameters,
        options: options,
      );
      return _handleResponse(response);
    } on DioException catch (e) {
      throw _handleDioError(e);
    } catch (e) {
      throw ApiException(message: e.toString());
    }
  }

  // Méthode POST
  Future<dynamic> post(
      String endpoint, {
        dynamic data,
        Map<String, dynamic>? queryParameters,
        Options? options,
        bool requiresAuth = true, // Ajoutez ce paramètre avec une valeur par défaut
      })async {
    try {
      final response = await _dio.post(
        endpoint,
        data: data,
        queryParameters: queryParameters,
        options: options,
      );
      return _handleResponse(response);
    } on DioException catch (e) {
      throw _handleDioError(e);
    } catch (e) {
      throw ApiException(message: e.toString());
    }
  }

  // Méthode PUT
  Future<dynamic> put(
      String endpoint, {
        dynamic data,
        Map<String, dynamic>? queryParameters,
        Options? options,
        bool requiresAuth = true, // Ajoutez ce paramètre avec une valeur par défaut
      })  async {
    try {
      final response = await _dio.put(
        endpoint,
        data: data,
        queryParameters: queryParameters,
        options: options,
      );
      return _handleResponse(response);
    } on DioException catch (e) {
      throw _handleDioError(e);
    } catch (e) {
      throw ApiException(message: e.toString());
    }
  }

  // Méthode DELETE
  Future<dynamic> delete(
      String endpoint, {
        dynamic data,
        Map<String, dynamic>? queryParameters,
        Options? options,
        bool requiresAuth = true, // Ajoutez ce paramètre avec une valeur par défaut
      }) async {
    try {
      final response = await _dio.delete(
        endpoint,
        data: data,
        queryParameters: queryParameters,
        options: options,
      );
      return _handleResponse(response);
    } on DioException catch (e) {
      throw _handleDioError(e);
    } catch (e) {
      throw ApiException(message: e.toString());
    }
  }

  // Traitement de la réponse
  dynamic _handleResponse(Response response) {
    if (response.statusCode! >= 200 && response.statusCode! < 300) {
      return response.data;
    } else {
      throw ApiException(
        message: response.data['message'] ?? 'Erreur inconnue',
        code: response.data['code'],
        statusCode: response.statusCode,
        data: response.data,
      );
    }
  }

  // Traitement des erreurs Dio
  ApiException _handleDioError(DioException error) {
    switch (error.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
        return ApiException.timeout();

      case DioExceptionType.badResponse:
        if (error.response != null) {
          switch (error.response!.statusCode) {
            case 400:
              return ApiException(
                message: error.response?.data['message'] ?? 'Requête invalide',
                code: error.response?.data['code'],
                statusCode: 400,
                data: error.response?.data,
              );
            case 401:
              return ApiException.unauthorized();
            case 403:
              return ApiException.forbidden();
            case 404:
              return ApiException.notFound();
            case 500:
            case 501:
            case 502:
            case 503:
              return ApiException.serverError();
            default:
              return ApiException(
                message: error.response?.data['message'] ?? 'Erreur serveur',
                code: error.response?.data['code'],
                statusCode: error.response?.statusCode,
                data: error.response?.data,
              );
          }
        }
        return ApiException.serverError();

      case DioExceptionType.cancel:
        return ApiException(
          message: 'Requête annulée',
          code: 'request_cancelled',
        );

      case DioExceptionType.connectionError:
      case DioExceptionType.unknown:
        if (error.error is SocketException) {
          return ApiException.networkError();
        }
        return ApiException(
          message: error.message ?? 'Erreur inconnue',
          code: 'unknown_error',
        );

      default:
        return ApiException(
          message: error.message ?? 'Erreur inconnue',
          code: 'unknown_error',
        );
    }
  }
}